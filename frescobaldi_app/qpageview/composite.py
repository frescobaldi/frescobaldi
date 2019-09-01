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
A Page with composite capabilities: to paint multiple pages over each other.

The Renderer acts as a composition manager; settings about how to combine
the pages are done in the renderer.

"""

import collections
import types
import weakref

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPainter, QPicture, QPixmap, QTransform

from . import page
from . import render



class CompositePage(page.AbstractPage):
    """A Page that can draw multiple pages over each other.

    The page that is painted first is put in the `base` attribute on
    instantiation, the other pages are appended to the `overlay` list.

    The base page dictates the dimensions and natural size of the
    CompositePage. The overlay pages are painted on top of the first page and
    positioned and scaled using the CompositePage.fit() method.

    Don't replace the overlay list later, but just change it; this makes
    sure that copied pages (e.g. the SidebarView or the Magnifier) use the
    correct information.

    A CompositePage has a renderer, but this one delegates the rendering
    to the "sub"pages, and just calls the paint() method of the sub pages. How
    those images are combined is up to the renderer.

    You should not use a sub Page from a CompositePage independently, as the
    CompositeRenderer modifies the position and dimensions. When you also want
    to use the original Page object, make a copy first.

    """
    def __init__(self, page=None, overlays=(), renderer=None):
        """Initialize with page and overlays.
        
        You can also set page and overlays later using setpages().
        
        """
        super().__init__()
        self.overlay = []
        if renderer is not None:
            self.renderer = renderer
        if page:
            self.setpages(page, overlays)

    def setpages(self, base, overlays):
        """Sets our base page and overlay pages."""
        self.base = base
        self.pageWidth = base.pageWidth
        self.pageHeight = base.pageHeight
        self.scaleX = base.scaleX
        self.scaleY = base.scaleY
        self.dpi = base.dpi
        self.overlay[:] = overlays
        
    def fitbase(self):
        """Make sure the base page has the same size as ourselves."""
        # base.x and y are not used
        self.base.width = self.width
        self.base.height = self.height
        self.base.scaleX = self.scaleX
        self.base.scaleY = self.scaleY
        self.base.computedRotation = self.computedRotation

    def fitoverlay(self, page):
        """Fits the overlay page in our page.

        By default this method centers the other page and scales it up
        as large as possible. The x and y coordinates of the overlay pages
        are used to specify their position relative to the base page.

        """
        page.computedRotation = (page.rotation + self.computedRotation) & 3
        s = page.defaultSize()

        scaleX = self.width / s.width()
        scaleY = self.height / s.height()
        scale = min(scaleX, scaleY)
        page.width = round(s.width() * scale)
        page.height = round(s.height() * scale)
        page.x = round((self.width - page.width) / 2)
        page.y = round((self.height - page.height) / 2)

    def fitpages(self):
        """Calls fitbase() and fitoverlay() for all overlay pages."""
        self.fitbase()
        for p in self.overlay:
            self.fitoverlay(p)

    def image(self, rect, dpiX=None, dpiY=None):
        """Return a QImage of the specified rectangle, of all images combined."""
        if dpiX is None:
            dpiX = self.dpi
        if dpiY is None:
            dpiY = dpiX
        self.fitpages()
        image = self.base.image(rect, dpiX, dpiY)
        overlays = []
        
        # find out the scale used for the image, to be able to position the
        # overlay images correctly (code copied from AbstractPage.image())
        s = self.defaultSize()
        hscale = s.width() * dpiX / self.dpi / self.width
        vscale = s.height() * dpiY / self.dpi / self.height
        ourscale = s.width() / self.width

        for p in self.overlay:
            overlayrect = rect & p.geometry()
            if overlayrect:
                # compute the correct resolution, find out which scale was
                # used by fitoverlay() (which may have been reimplemented)
                overlaywidth = p.pageWidth * p.scaleX * self.dpi / p.dpi
                if p.computedRotation & 1:
                    overlayscale = overlaywidth / p.height
                else:
                    overlayscale = overlaywidth / p.width
                scale = ourscale / overlayscale
                img = p.image(overlayrect.translated(-p.pos()), dpiX * scale, dpiY * scale)
                pos = overlayrect.topLeft() - rect.topLeft()
                pos = QPoint(round(pos.x() * hscale), round(pos.y() * vscale))
                overlays.append((pos, img))

        return self.renderer.composite(image, overlays)

    def print(self, painter, rect=None):
        """Prints the composite page."""
        self.fitpages()
        
        transform = painter.transform()
        
        basepict = QPicture()
        p = QPainter(basepict)
        p.setTransform(transform)   # now the other print routines know the underlying resolution
        self.base.print(p, rect)
        
        overlays = []
        for p in self.overlay:
            pass #TODO print the overlay pages to QPictures
        
        painter.setTransform(QTransform())  # remove the transform
        self.renderer.composite(basepict, overlays).play(painter)

    def text(self, rect):
        """Reimplemented to return the text from the base Page."""
        self.fitbase() # make sure the rect is understood correctly
        return self.base.text(rect)

    def links(self):
        """Reimplemented to return the links from the base Page."""
        return self.base.links()


class CompositeRenderer(render.AbstractImageRenderer):
    """Paints the pages by calling their own renderer."""

    def __init__(self):
        super().__init__()
        self._callbacks = weakref.WeakKeyDictionary()
        self.opacity = [0.5]

    def makecallback(self, callback, page):
        """Return a callback for the composite page, the same if possible.

        This callback is called when rendering a base or overlay page is
        finished, and in turn it calls the original callback with the original
        composite page.

        We cache the callback using a weak reference; this makes sure that
        unscheduling rendering jobs works correctly.

        """
        # household: first remove dead refs from all page dicts
        deadcallbacks = [(r, page)
                            for page, d in self._callbacks.items()
                                for r in d if r() is None]
        for r, page in deadcallbacks:
            del self._callbacks[page][r]
            if not self._callbacks[page]:
                del self._callbacks[page]

        # make a weak ref to the callback
        if type(callback) is types.MethodType:
            callbackref = weakref.WeakMethod(callback)
        else:
            callbackref = weakref.ref(callback)

        # return the existing callback or create one
        try:
            return self._callbacks[page][callbackref]
        except KeyError:
            pageref = weakref.ref(page)
            def newcallback(p):
                """Called when a subpage (base or overlay) of page has been rendered."""
                page = pageref()
                callback = callbackref()
                if page is not None and callback is not None:
                    callback(page)
            self._callbacks.setdefault(page, {})[callbackref] = newcallback
            return newcallback

    def update(self, page, device, rect, callback=None):
        """Reimplemented to check/rerender (if needed) all sub pages."""
        if not rect:
            return  True    # just in case

        # make the call back return with the original page, not the overlay page
        newcallback = self.makecallback(callback, page) if callback else None
        # position the subpages correctly
        page.fitpages()

        ok = True
        if page.base.renderer and not page.base.renderer.update(page.base, device, rect, newcallback):
            ok = False

        for p in page.overlay:
            overlayrect = (rect & p.geometry()).translated(-p.pos())
            if overlayrect and p.renderer and not p.renderer.update(p, device, overlayrect, newcallback):
                ok = False
        return ok

    def paint(self, page, painter, rect, callback=None):
        """Paint the sub pages on pixmaps, and then combine them."""
        if not rect:
            return  # just in case

        # make the call back return with the original page, not the overlay page
        newcallback = self.makecallback(callback, page) if callback else None
        # position the subpages correctly
        page.fitpages()

        # get the device pixel ratio to paint for
        try:
            ratio = painter.device().devicePixelRatioF()
        except AttributeError:
            ratio = painter.device().devicePixelRatio()

        # let base page draw on a pixmap
        bpixmap = QPixmap(rect.size() * ratio)
        bpixmap.setDevicePixelRatio(ratio)
        pt = QPainter(bpixmap)
        pt.translate(-rect.topLeft())
        page.base.paint(pt, rect, newcallback)
        pt.end()
        
        overlays = []

        # draw the overlay pages on pixmaps
        for p in page.overlay:
            overlayrect = (rect & p.geometry()).translated(-p.pos())
            if overlayrect:
                opixmap = QPixmap(overlayrect.size() * ratio)
                opixmap.setDevicePixelRatio(ratio)
                pt = QPainter(opixmap)
                pt.translate(-overlayrect.topLeft())
                p.paint(pt, overlayrect, newcallback)
                pt.end()

                pos = overlayrect.topLeft() + p.pos() - rect.topLeft()
                overlays.append((pos, opixmap))
        
        # draw the combined pixmap
        painter.drawPixmap(rect.topLeft(), self.composite(bpixmap, overlays))

    def unschedule(self, pages, callback):
        """Reimplemented to unschedule base and overlay pages."""
        def unschedule_page(page, cb):
            if page.renderer:
                page.renderer.unschedule((page,), cb)
        for page in pages:
            newcallback = self.makecallback(callback, page) if callback else None
            unschedule_page(page.base, newcallback)
            for p in page.overlay:
                unschedule_page(p, newcallback)
    
    def invalidate(self, pages):
        """Reimplemented to invalidate the base and overlay pages."""
        renderers = collections.defaultdict(list)
        for page in pages:
            for p in [page.base] + page.overlay:
                if p.renderer:
                    renderers[p.renderer].append(p)
        for renderer, pages in renderers.items():
            renderer.invalidate(pages)
    
    def composite(self, base, overlays):
        """Paints the overlays over the base image.
        
        overlays is an interable of tuples (pos, image). The images can be of
        type QPixmap or QImage.
        
        The resulting image is returned and is of the same type as the base
        image. The implementation may choose to paint directly on the base
        image and return it, but the returned image can also be a new one.
        
        """
        ### NOTE: If you return a new image, set it to the same device pixel
        ### ratio as the original base image
        
        ### TODO: move compositing to a specific class and add much
        ### more options
        painter = QPainter(base)
        for layer, (pos, img) in enumerate(overlays):
            painter.setOpacity(self.opacity[layer])
            if isinstance(img, QPixmap):
                painter.drawPixmap(pos, img)
            elif isinstance(img, QPicture):
                painter.drawPicture(pos, img)
            else:
                painter.drawImage(pos, img)
        return base



# install a default renderer, so CompositePage can be used directly
CompositePage.renderer = CompositeRenderer()



