# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
A MultiPage has no contents itself (but it has a size!), and renders a list of
embedded pages.

The MultiPageRenderer has the same interface as an ordinary renderer, but defers
rendering to the renderer of the embedded pages.

"""

import collections

from PyQt5.QtCore import QPoint, QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap, QRegion, QTransform

from . import page
from . import render



class MultiPage(page.AbstractPage):
    """A special Page that has a list of embedded sub pages.

    The sub pages are in the pages attribute, the first one is on top.

    The position and size of the embedded pages is set in the updateSize()
    method, which is inherited from AbstractPage. By default all sub pages
    are centered in their natural size.
    
    Rotation of sub pages is relative to the MultiPage.

    The `scalePages` instance attribute can be used to multiply the zoomfactor
    for the sub pages.

    The `opaquePages` instance attribute optimizes some procedures when set to
    True (i.e. it prevents rendering sub pages that are hidden below others).

    """

    scalePages = 1.0
    opaquePages = True


    def __init__(self, renderer=None):
        self.pages = []
        if renderer is not None:
            self.renderer = renderer

    def copy(self, owner=None, matrix=None):
        """Reimplemented to also copy the sub pages."""
        page = super().copy(owner, matrix)
        page.pages = [p.copy(owner, matrix) for p in self.pages]
        return page

    def updateSize(self, dpiX, dpiY, zoomFactor):
        """Reimplemented to also position our sub-pages.

        The default implementation of this method zooms the sub pages
        at the zoom level of the page * self.scalePages.

        """
        super().updateSize(dpiX, dpiY, zoomFactor)

        # zoom the sub pages, using the same zoomFactor
        for page in self.pages:
            page.computedRotation = (page.rotation + self.computedRotation) & 3
            page.updateSize(dpiX, dpiY, zoomFactor * self.scalePages)

        self.updatePagePositions()

    def updatePagePositions(self):
        """Called by updateSize(), set the page positions.

        The default implementation of this method centers the pages.

        """
        # center the pages
        center = self.rect().center()
        for page in self.pages:
            r = page.rect()
            r.moveCenter(center)
            page.setGeometry(r)

    def visiblePagesAt(self, rect):
        """Yield (page, rect) for all subpages that ly in rect.

        If opaquePages is True, excludes pages hidden below others.

        """
        covered = QRegion()
        for p in self.pages:
            overlayrect = rect & p.geometry()
            if overlayrect:
                if self.opaquePages and not QRegion(overlayrect).subtracted(covered):
                    continue    # skip if this part is hidden below the other
                covered += overlayrect
                yield p, overlayrect
                if self.opaquePages and not QRegion(rect).subtracted(covered):
                    break

    def printablePagesAt(self, rect):
        """Yield (page, matrix) for all subpages that are visible in rect.

        If opaquePages is True, excludes pages hidden below others. The matrix
        (QTransform) describes the transformation from the page to the sub
        page. Rect is in original coordinates, as with the print() method.

        """
        origmatrix = self.transform().inverted()[0] # map pos to original page
        origmatrix.scale(self.scaleX, self.scaleY)  # undo the scaling done in printing.py
        for p, r in self.visiblePagesAt(self.mapToPage().rect(rect)):
            center = origmatrix.map(QRectF(p.geometry()).center())
            m = QTransform()    # matrix from page to subpage
            m.translate(center.x(), center.y())
            m.rotate(p.rotation * 90) # rotation relative to us
            m.scale(
                self.scalePages * p.scaleX * self.dpi / p.dpi,
                self.scalePages * p.scaleY * self.dpi / p.dpi)
            m.translate(p.pageWidth / -2, p.pageHeight / -2)
            yield p, m

    def print(self, painter, rect=None, paperColor=None):
        """Prints our sub pages."""
        if self.renderer:
            if rect is None:
                rect = self.pageRect()
            self.renderer.print(self, painter, rect, paperColor)


class MultiPageRenderer(render.AbstractImageRenderer):
    """A renderer that interfaces with the renderers of the sub pages of a MultiPage."""
    def update(self, page, device, rect, callback=None):
        """Reimplemented to check/rerender (if needed) all sub pages."""
        # make the call back return with the original page, not the overlay page
        newcallback = CallBack(callback, page) if callback else None

        ok = True
        for p, overlayrect in page.visiblePagesAt(rect):
            if p.renderer and not p.renderer.update(p, device, overlayrect.translated(-p.pos()), newcallback):
                ok = False
        return ok

    def print(self, page, painter, rect, paperColor):
        """Print the sub pages at the correct position."""
        painter.save()
        painter.translate(-rect.topLeft())
        # print from bottom to top
        for p, m in reversed(list(page.printablePagesAt(rect))):
            # find center of the page corresponding to our center
            painter.save()
            painter.setTransform(m, True)
            # handle rect clipping
            clip = m.inverted()[0].mapRect(rect) & p.pageRect()
            painter.fillRect(clip, paperColor or Qt.white)    # draw a white background
            painter.translate(clip.topLeft())   # the page will go back...
            p.print(painter, clip)
            painter.restore()
        painter.restore()

    def paint(self, page, painter, rect, callback=None):
        """Reimplemented to paint all the sub pages on top of each other."""
        # make the call back return with the original page, not the overlay page
        newcallback = CallBack(callback, page) if callback else None

        # get the device pixel ratio to paint for
        try:
            ratio = painter.device().devicePixelRatioF()
        except AttributeError:
            ratio = painter.device().devicePixelRatio()

        pixmaps = []
        covered = QRegion()
        for p, overlayrect in page.visiblePagesAt(rect):
            pixmap = QPixmap(overlayrect.size() * ratio)
            pixmap.setDevicePixelRatio(ratio)
            pt = QPainter(pixmap)
            pt.translate(p.pos() - overlayrect.topLeft())
            p.paint(pt, overlayrect.translated(-p.pos()), newcallback)
            pt.end()

            pos = overlayrect.topLeft()
            pixmaps.append((pos, pixmap))
            covered += overlayrect

        if QRegion(rect).subtracted(covered):
            painter.fillRect(rect, page.paperColor or self.paperColor)

        self.combine(painter, pixmaps)

    def image(self, page, rect, dpiX, dpiY, paperColor):
        """Return a QImage of the specified rectangle, of all images combined."""

        overlays = []

        # find out the scale used for the image, to be able to position the
        # overlay images correctly (code copied from AbstractImageRenderer.image())
        s = page.defaultSize()
        hscale = s.width() * dpiX / page.dpi / page.width
        vscale = s.height() * dpiY / page.dpi / page.height
        ourscale = s.width() / page.width

        for p, overlayrect in page.visiblePagesAt(rect):
            # compute the correct resolution, find out which scale was
            # used by updateSize() (which may have been reimplemented)
            overlaywidth = p.pageWidth * p.scaleX * page.dpi / p.dpi
            if p.computedRotation & 1:
                overlayscale = overlaywidth / p.height
            else:
                overlayscale = overlaywidth / p.width
            scale = ourscale / overlayscale
            img = p.image(overlayrect.translated(-p.pos()), dpiX * scale, dpiY * scale, paperColor)
            pos = overlayrect.topLeft() - rect.topLeft()
            pos = QPoint(round(pos.x() * hscale), round(pos.y() * vscale))
            overlays.append((pos, img))

        image = QImage(rect.width() * hscale, rect.height() * vscale, self.imageFormat)
        image.fill(paperColor or page.paperColor or self.paperColor)
        self.combine(QPainter(image), overlays)
        return image

    def unschedule(self, pages, callback):
        """Reimplemented to unschedule all sub pages."""
        for page in pages:
            newcallback = CallBack(callback, page) if callback else None
            for p in page.pages:
                if p.renderer:
                    p.renderer.unschedule((p,), newcallback)

    def invalidate(self, pages):
        """Reimplemented to invalidate the base and overlay pages."""
        renderers = collections.defaultdict(list)
        for page in pages:
            for p in page.pages:
                if p.renderer:
                    renderers[p.renderer].append(p)
        for renderer, pages in renderers.items():
            renderer.invalidate(pages)

    def combine(self, painter, images):
        """Paints images on the painter.

        Each image is a tuple(QPoint, QPixmap), describing where to draw.
        The image on top is first, so drawing should start with the last.

        """
        for pos, image in reversed(images):
            if isinstance(image, QPixmap):
                painter.drawPixmap(pos, image)
            else:
                painter.drawImage(pos, image)


class CallBack:
    """A wrapper for a callable that is called with the original Page."""
    def __new__(cls, origcallable, page):
        # if the callable is already a CallBack instance, just return it. This
        # would happen if a MultiPage has a subpage that is also a MultiPage.
        if cls == type(origcallable):
            return origcallable
        cb = object.__new__(cls)
        cb.origcallable = origcallable
        cb.page = page
        return cb

    def __hash__(self):
        """Return the hash of the original callable.

        This way only one callback will be in the Job.callbacks attribute,
        despite of multiple pages, and unscheduling a job with subpages still
        works.

        """
        return hash(self.origcallable)

    def __call__(self, page):
        """Call the original callback with the original Page."""
        self.origcallable(self.page)



# install a default renderer, so MultiPage can be used directly
MultiPage.renderer = MultiPageRenderer()

