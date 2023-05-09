# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
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
A Page is responsible for drawing a page inside a PageLayout.

"""

import weakref

from PyQt5.QtCore import QBuffer, QPointF, QRect, QRectF, QSizeF, Qt
from PyQt5.QtGui import (
    QColor, QImage, QPageSize, QPainter, QPdfWriter, QPixmap, QTransform)
from PyQt5.QtSvg import QSvgGenerator

from . import util
from .constants import Rotate_0


# a cache to store "owned" copies
_copycache = weakref.WeakKeyDictionary()


class AbstractPage(util.Rectangular):
    """A Page is a rectangle that is positioned in a PageLayout.

    A Page represents one page, added to a PageLayout that is displayed in a
    View. Although there is no mechanism to enforce it, a Page is normally only
    used in one PageLayout at a time.

    A Page has instance attributes:

    * that normally do not change during its lifetime:

        `pageWidth`
            the original width  (by default in points, `dpi` is 72.0
        `pageHeight`
            the original height   but can be changed at class level)

    * that can be modified by the user (having defaults at the class level):

        `scaleX`
            the scale in X-direction of the original page (1.0)
        `scaleY`
            the scale in Y-direction of the original page (1.0)
        `rotation`
            the rotation (Rotate_0)
        `z`
            the z-index (0) (only relevant when pages overlap)
        `paperColor`
            the paper color (None). If None, the renderer's
            paperColor is used.

    * and that are set by the layout when computing the size and positioning
      the pages:

        `x`
            the position x-coordinate
        `y`
            the position y-coordinate
        `width`
            the width in pixels
        `height`
            the height in pixels
        `computedRotation`
            the rotation in which finally to render

    The class variable `dpi` is 72.0 by default but can be set to a different
    value depending on the page type. E.g. for Svg pages 90 or 96 makes sense.

    """
    renderer = None
    dpi = 72.0
    pageWidth = 595.28         # default to A4
    pageHeight = 841.89

    z = 0
    rotation = Rotate_0
    computedRotation = Rotate_0
    scaleX = 1.0
    scaleY = 1.0
    paperColor = None

    @classmethod
    def load(cls, filename, renderer=None):
        """Implement this to yield one or more pages by reading the file.

        The renderer may be None, and not all page types use a renderer.
        The filename may be a string or a QByteArray object containing the
        data.

        """
        pass

    @classmethod
    def loadFiles(cls, filenames, renderer=None):
        """Load multiple files, yielding Page instances of this type."""
        for f in filenames:
            for page in cls.load(f, renderer):
                yield page

    def copy(self, owner=None, matrix=None):
        """Return a copy of the page with the same instance attributes.

        If owner is specified, the copy is weakly cached for that owner and
        returned next time. All instance attribute will be updated each time.
        If matrix is specified, it should be a QTransform, and it will be used
        to map the geometry of the original to the (cached) copy before it is
        returned.

        """
        cls = type(self)
        if owner:
            try:
                page = _copycache[owner][self]
            except KeyError:
                page = cls.__new__(cls)
                _copycache.setdefault(owner, weakref.WeakKeyDictionary())[self] = page
            else:
                page.__dict__.clear()
        else:
            page = cls.__new__(cls)
        page.__dict__.update(self.__dict__)
        if matrix:
            page.setGeometry(matrix.mapRect(self.geometry()))
        return page

    def setPageSize(self, sizef):
        """Set our natural page size (QSizeF).

        Normally this is done in the constructor, based on the page we need to
        render.

        By default the page size is assumed to be in points, 1/72 of an inch.
        You can set the `dpi` class variable to use a different unit.

        """
        self.pageWidth = sizef.width()
        self.pageHeight = sizef.height()

    def pageSize(self):
        """Return our natural page size (QSizeF).

        By default the page size is assumed to be in points, 1/72 of an inch.
        You can set the `dpi` class variable to use a different unit.

        """
        return QSizeF(self.pageWidth, self.pageHeight)

    def pageRect(self):
        """Return QRectF(0, 0, pageWidth, pageHeight)."""
        return QRectF(0, 0, self.pageWidth, self.pageHeight)

    def transform(self, width=None, height=None):
        """Return a QTransform, converting an original area to page coordinates.

        The `width` and `height` refer to the original (unrotated) width and
        height of the page's contents, and default to pageWidth and pageHeight.

        """
        if width  is None: width  = self.pageWidth
        if height is None: height = self.pageHeight
        t = QTransform()
        t.scale(self.width, self.height)
        t.translate(.5, .5)
        t.rotate(self.computedRotation * 90)
        t.translate(-.5, -.5)
        t.scale(1 / width, 1 / height)
        return t

    def defaultSize(self):
        """Return the pageSize() scaled and rotated (if needed).

        Based on scaleX, scaleY, and computedRotation attributes.

        """
        s = QSizeF(self.pageWidth * self.scaleX, self.pageHeight * self.scaleY)
        if self.computedRotation & 1:
            s.transpose()
        return s

    def updateSize(self, dpiX, dpiY, zoomFactor):
        """Set the width and height attributes of the page.

        This size is computed based on the page's natural size, dpi, scale and
        computedRotation attribute; and the supplied dpiX, dpiY, and zoomFactor.

        """
        s = self.defaultSize()
        # now handle dpi, scale and zoom
        self.width = round(s.width() * dpiX / self.dpi * zoomFactor)
        self.height = round(s.height() * dpiY / self.dpi * zoomFactor)

    def zoomForWidth(self, width, rotation, dpiX):
        """Return the zoom we need to display ourselves at the given width."""
        width = max(width, 1)
        if (self.rotation + rotation) & 1:
            w = self.pageHeight / self.scaleY
        else:
            w = self.pageWidth / self.scaleX
        return width * self.dpi / dpiX / w

    def zoomForHeight(self, height, rotation, dpiY):
        """Return the zoom we need to display ourselves at the given height."""
        height = max(height, 1)
        if (self.rotation + rotation) & 1:
            h = self.pageWidth / self.scaleX
        else:
            h = self.pageHeight / self.scaleY
        return height * self.dpi / dpiY / h

    def paint(self, painter, rect, callback=None):
        """Implement this to paint our Page.

        The View calls this method in the paint event. If you can't paint
        quickly, just return and schedule an image to be rendered in the
        background. If a callback is specified, it is called when the image
        is ready with the page as argument.

        """
        pass

    def print(self, painter, rect=None, paperColor=None):
        """Implement this to paint a page for printing.

        The difference with paint() and image() is that the rect (QRectF)
        supplied to print() is not in the Page coordinates, but in the original
        pageSize() and unrotated. The painter has been prepared for scale and
        rotation.

        If rect is None, the full pageRect() is used.

        """
        pass

    def output(self, device, rect=None, paperColor=None):
        """Paint specified rectangle (or the whole page) to the paint device.

        The page is rotated and scaled, and the resolution of the paint device
        is used in case pixelbased images need to be generated. But where
        possible, vector painting is used.

        This method uses :meth:`print` to do the actual painting to the paint
        device. If paperColor is not given, no background is printed normally.

        """
        if rect is None:
            rect = self.pageRect()
        painter = QPainter(device)
        painter.scale(device.logicalDpiX() / self.dpi, device.logicalDpiY() / self.dpi)
        util.rotate(painter, self.computedRotation, rect.width(), rect.height())
        painter.scale(self.scaleX, self.scaleY)
        self.print(painter, rect, paperColor)
        return painter.end()

    def image(self, rect=None, dpiX=None, dpiY=None, paperColor=None):
        """Implement this to return a QImage of the specified rectangle.

        The rectangle is relative to our top-left position. dpiX defaults to
        our default dpi and dpiY defaults to dpiX.

        """
        pass

    def pdf(self, filename, rect=None, resolution=72.0, paperColor=None):
        """Create a PDF file for the selected rect or the whole page.

        The filename may be a string or a QIODevice object. The rectangle is
        relative to our top-left position. Normally vector graphics are
        rendered, but in cases where that is not possible, the resolution will
        be used to determine the DPI for the generated rendering.

        """
        # map to the original page
        source = self.pageRect() if rect is None else self.mapFromPage().rect(rect)
        # scale to target size
        w = source.width() * self.scaleX
        h = source.height() * self.scaleY
        if self.computedRotation & 1:
            w, h = h, w
        targetSize = QSizeF(w, h)

        pdf = QPdfWriter(filename)
        pdf.setCreator("qpageview")
        pdf.setResolution(int(resolution))

        layout = pdf.pageLayout()
        layout.setMode(layout.FullPageMode)
        layout.setPageSize(QPageSize(targetSize * 72.0 / self.dpi, QPageSize.Point))
        pdf.setPageLayout(layout)
        return self.output(pdf, source, paperColor)

    def eps(self, filename, rect=None, resolution=72.0, paperColor=None):
        """Create a EPS (Encapsulated Postscript) file for the selected rect or the whole page.

        This needs the popplerqt5 module.
        The filename may be a string or a QIODevice object. The rectangle is
        relative to our top-left position. Normally vector graphics are
        rendered, but in cases where that is not possible, the resolution will
        be used to determine the DPI for the generated rendering.

        """
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        success = self.pdf(buf, rect, resolution, paperColor)
        buf.close()
        if success:
            from . import poppler
            for pdf in poppler.PopplerPage.load(buf.data()):
                ps = pdf.document.psConverter()
                ps.setPageList([pdf.pageNumber+1])
                if isinstance(filename, str):
                    ps.setOutputFileName(filename)
                else:
                    ps.setOutputDevice(filename)
                try:
                    ps.setPSOptions(ps.PSOption(ps.Printing | ps.StrictMargins))
                    ps.setPSOptions(ps.PSOption(ps.Printing | ps.StrictMargins | ps.PrintToEPS))
                except AttributeError:
                    pass
                ps.setVDPI(resolution)
                ps.setHDPI(resolution)
                return ps.convert()
        return False

    def svg(self, filename, rect=None, resolution=72.0, paperColor=None):
        """Create a SVG file for the selected rect or the whole page.

        The filename may be a string or a QIODevice object. The rectangle is
        relative to our top-left position. Normally vector graphics are
        rendered, but in cases where that is not possible, the resolution will
        be used to determine the DPI for the generated rendering.

        """
        # map to the original page
        source = self.pageRect() if rect is None else self.mapFromPage().rect(rect)
        # scale to target size
        w = source.width() * self.scaleX
        h = source.height() * self.scaleY
        if self.computedRotation & 1:
            w, h = h, w
        targetSize = QSizeF(w, h) * resolution / self.dpi

        svg = QSvgGenerator()
        if isinstance(filename, str):
            svg.setFileName(filename)
        else:
            svg.setOutputDevice(filename)
        svg.setResolution(int(resolution))
        svg.setSize(targetSize.toSize())
        svg.setViewBox(QRectF(0, 0, targetSize.width(), targetSize.height()))
        return self.output(svg, source, paperColor)

    def pixmap(self, rect=None, size=100, paperColor=None):
        """Return a QPixmap, scaled so that width or height doesn't exceed size.

        Uses the :meth:`image` method to get the image, and converts that to a
        QPixmap.

        """
        s = self.defaultSize()
        w, h = s.width(), s.height()
        if rect is not None:
            w *= rect.width() / self.width
            h *= rect.height() / self.height
        l = max(w, h)
        dpi = size / l * self.dpi
        return QPixmap.fromImage(self.image(rect, dpi, dpi, paperColor))

    def mutex(self):
        """Return an object that should be locked when rendering the page.

        Page are guaranteed not to be rendered at the same time when they
        return the same mutex object. By default, None is returned.

        """

    def group(self):
        """Return the group the page belongs to.

        This could be some document structure, so that different Page objects
        could refer to the same graphical contents, preventing double caching.

        This object is used together with the value returned by ident() as a key
        to cache the page. The idea is that the contents of the page are
        uniquely identified by the objects returned by group() and ident().

        This way, when the same document is opened in multiple page instances,
        only one copy resides in the (global) cache.

        By default, the page object itself is returned.

        """
        return self

    def ident(self):
        """Return a value that identifies the page within the group returned
        by group().

        By default, None is returned.

        """
        return None

    def mapToPage(self, width=None, height=None):
        """Return a MapToPage object, that can map original to Page coordinates.

        The `width` and `height` refer to the original (unrotated) width and
        height of the page's contents, and default to pageWidth and pageHeight.

        """
        return util.MapToPage(self.transform(width, height))

    def mapFromPage(self, width=None, height=None):
        """Return a MapFromPage object, that can map Page to original coordinates.

        The `width` and `height` refer to the original (unrotated) width and
        height of the page's contents, and default to pageWidth and pageHeight.

        """
        return util.MapFromPage(self.transform(width, height).inverted()[0])

    def text(self, rect):
        """Implement this method to get the text at the specified rectangle.

        The rectangle should be in page coordinates. The default implementation
        simply returns an empty string.

        """
        return ""

    def getLinks(self):
        """Implement this method to load our links."""
        from . import link
        return link.Links()

    def links(self):
        """Return the Links object, containing Link objects.

        Every Link denotes a clickable area on a Page, in coordinates 0.0-1.0.
        The Links object makes it possible to quickly find a link on a Page.
        This is cached after the first request, you should implement the
        getLinks() method to load the links.

        """
        try:
            return self._links
        except AttributeError:
            links = self._links = self.getLinks()
        return links

    def linksAt(self, point):
        """Return a list of zero or more links touched by QPoint point.

        The point is in page coordinates.
        The list is sorted with the smallest rectangle first.

        """
        # Link objects have their area ranging
        # in width and height from 0.0 to 1.0 ...
        pos = self.mapFromPage(1, 1).point(point)
        links = self.links()
        return sorted(links.at(pos.x(), pos.y()), key=links.width)

    def linksIn(self, rect):
        """Return an unordered set of links enclosed in rectangle.

        The rectangle is in page coordinates.

        """
        return self.links().inside(*self.mapFromPage(1, 1).rect(rect).getCoords())

    def linkRect(self, link):
        """Return a QRect encompassing the linkArea of a link in coordinates of our page."""
        return self.mapToPage(1, 1).rect(link.rect())


class AbstractRenderedPage(AbstractPage):
    """A Page that has a renderer that performs caching and painting.

    The renderer lives in the renderer attribute.

    """
    def __init__(self, renderer=None):
        if renderer is not None:
            self.renderer = renderer

    def paint(self, painter, rect, callback=None):
        """Reimplement this to paint our Page.

        The View calls this method in the paint event. If you can't paint
        quickly, just return and schedule an image to be rendered in the
        background. If a callback is specified, it is called when the image
        is ready with the page as argument.

        By default, this method calls the renderer's
        :meth:`~.render.AbstractRenderer.paint` method.

        """
        if rect:
            self.renderer.paint(self, painter, rect, callback)

    def print(self, painter, rect=None, paperColor=None):
        """Paint a page for printing.

        The difference with :meth:`paint` and :meth:`image` is that the rect
        (QRectF) supplied to print() is not in the Page coordinates, but in the
        original pageSize() and unrotated. The painter has been prepared for
        scale and rotation.

        If rect is None, the full pageRect() is used.
        This method calls the renderer's draw() method.

        """
        if rect is None:
            rect = self.pageRect()
        else:
            rect = rect & self.pageRect()
        from . import render
        k = render.Key(self.group(), self.ident(), 0, self.pageWidth, self.pageHeight)
        t = render.Tile(*rect.normalized().getRect())
        self.renderer.draw(self, painter, k, t, paperColor)

    def image(self, rect=None, dpiX=None, dpiY=None, paperColor=None):
        """Returns a QImage of the specified rectangle.

        The rectangle is relative to our top-left position. dpiX defaults to
        our default dpi and dpiY defaults to dpiX. This implementation calls
        the renderer to generate the image. The image is not cached.

        """
        if rect is None:
            rect = self.rect()
        if dpiX is None:
            dpiX = self.dpi
        if dpiY is None:
            dpiY = dpiX
        return self.renderer.image(self, rect, dpiX, dpiY, paperColor)


class BlankPage(AbstractPage):
    """A blank page."""
    def paint(self, painter, rect, callback=None):
        """Paint blank page in the View."""
        painter.fillRect(rect, self.paperColor or Qt.white)

    def print(self, painter, rect=None, paperColor=None):
        """Paint blank page for printing."""
        if rect is None:
            rect = self.pageRect()
        else:
            rect = rect & self.pageRect()
        painter.fillRect(rect, paperColor or Qt.white)

    def image(self, rect=None, dpiX=None, dpiY=None, paperColor=None):
        """Return a blank image."""
        if rect is None:
            rect = self.rect()
        if dpiX is None:
            dpiX = self.dpi
        if dpiY is None:
            dpiY = dpiX
        s = self.defaultSize()
        width = s.width() * dpiX / self.dpi
        height = s.height() * dpiY / self.dpi
        image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        image.fill(paperColor or Qt.white)
        return image


class ImagePrintPageMixin:
    """A Page mixin that implements print() using the image() method.

    This can be used e.g. for compositing pages, which does not work well
    when painting to a PDF, a printer or a SVG generator.

    """
    def print(self, painter, rect=None, paperColor=None):
        """Print using the image() method."""
        if rect is None:
            rect = self.pageRect()
        else:
            rect = rect & self.pageRect()
        # Find the rectangle on the Page in page coordinates
        target = self.mapToPage().rect(rect)
        # Make an image exactly in the printer's resolution
        m = painter.transform()
        r = m.mapRect(rect)       # see where the rect ends up
        w, h = r.width(), r.height()
        if m.m11() == 0:
            w, h = h, w     # swap if rotation & 1  :-)
        # now we know the scale from our dpi to the paintdevice's logicalDpi!
        hscale = w / rect.width()
        vscale = h / rect.height()
        dpiX = self.dpi * hscale
        dpiY = self.dpi * vscale
        image = self.image(target, dpiX, dpiY, paperColor)
        painter.translate(-rect.topLeft())
        painter.drawImage(rect, image)


