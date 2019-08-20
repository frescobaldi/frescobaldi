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

import types
import weakref

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPainter, QPixmap

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
    def __init__(self, page, renderer=None):
        super().__init__()
        self.base = page
        self.overlay = []
        self.pageWidth = page.pageWidth
        self.pageHeight = page.pageHeight
        self.scaleX = page.scaleX
        self.scaleY = page.scaleY
        if renderer is not None:
            self.renderer = renderer

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
        pageWidth = page.pageWidth * page.scaleX
        pageHeight = page.pageHeight * page.scaleY
        page.computedRotation = (page.rotation + self.computedRotation) & 3
        if page.computedRotation & 1:
            pageWidth, pageHeight = pageHeight, pageWidth

        scaleX = self.width / pageWidth
        scaleY = self.height / pageHeight
        scale = min(scaleX, scaleY)
        page.width = pageWidth * scale
        page.height = pageHeight * scale
        page.x = (self.width - page.width) // 2
        page.y = (self.height - page.height) // 2

    def fitpages(self):
        """Calls fitbase() and fitoverlay() for all overlay pages."""
        self.fitbase()
        for p in self.overlay:
            self.fitoverlay(p)

    def image(self, rect, dpiX=72.0, dpiY=None):
        """Return a QImage of the specified rectangle, of all images combined."""
        if dpiY is None:
            dpiY = dpiX
        self.fitpages()
        image = self.base.image(rect, dpiX, dpiY)
        painter = QPainter(image)
        for layer, p in enumerate(self.overlay):
            overlayrect = rect & p.geometry()
            if overlayrect:
                # compute the correct resolution, find out which scale was
                # used by fitoverlay() (which may have been reimplemented)
                if p.computedRotation & 1:
                    overlayscale = p.pageWidth * p.scaleX / p.height
                else:
                    overlayscale = p.pageWidth * p.scaleX / p.width
                if self.computedRotation & 1:
                    ourscale = self.pageWidth * self.scaleX / self.height
                else:
                    ourscale = self.pageWidth * self.scaleX / self.width
                scale = ourscale / overlayscale
                img = p.image(overlayrect.translated(-p.pos()), dpiX * scale, dpiY * scale)

                painter.save()
                painter.setOpacity(self.renderer.opacity[layer])
                painter.drawImage(overlayrect.topLeft() - rect.topLeft(), img)
                painter.restore()
        painter.end()
        return image

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

        # let page draw on a pixmap
        pixmap = QPixmap(rect.size() * ratio)
        pixmap.setDevicePixelRatio(ratio)
        pt = QPainter(pixmap)
        pt.translate(-rect.topLeft())
        page.base.paint(pt, rect, newcallback)
        pt.end()

        # first paint the base page
        painter.setOpacity(1)
        painter.drawPixmap(rect.topLeft(), pixmap)

        # paint the overlay pages on top
        for layer, p in enumerate(page.overlay):
            # draw on a pixmap
            overlayrect = (rect & p.geometry()).translated(-p.pos())
            if overlayrect:
                pixmap = QPixmap(overlayrect.size() * ratio)
                pixmap.setDevicePixelRatio(ratio)
                pt = QPainter(pixmap)
                pt.translate(-overlayrect.topLeft())
                p.paint(pt, overlayrect, newcallback)
                pt.end()

                # paint the overlay page
                painter.save()
                painter.setOpacity(self.opacity[layer])
                painter.drawPixmap(overlayrect.topLeft() + p.pos(), pixmap)
                painter.restore()

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



# install a default renderer, so CompositePage can be used directly
CompositePage.renderer = CompositeRenderer()



