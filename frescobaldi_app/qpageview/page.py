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

import copy

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PyQt5.QtGui import QColor

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)




class AbstractPage:
    """A Page is a rectangle that is positioned in a PageLayout.

    A Page represents one page, added to a PageLayout that is displayed in a
    View. Although there is no mechanism to enforce it, a Page is normally only
    used in one PageLayout at a time.

    A Page has instance attributes...

    ...that normally do not change during its lifetime:

        `pageWidth`     the original width in points (1/72 inch)
        `pageHeight`    the original height in points (1/72 inch)

    ... that can be modified by the user (having defaults at the class level):

        `rotation`      the rotation (Rotate_0)
        `scaleX`        the scale in X-direction (1.0)
        `scaleY`        the scale in Y-direction (1.0)
        `paperColor`    the paper color (None). If None, the renderer's
                        paperColor is used.

    ... and that are set by the layout when computing the size and positioning
        the pages:

        `x`             the position x-coordinate
        `y`             the position y-coordinate
        `width`         the width in pixels
        `height`        the height in pixels
        `computedRotation` the rotation in which finally to render

    A page is rendered by a renderer, which can live in a class
    or instance attribute.


    """

    renderer = None

    rotation = Rotate_0
    scaleX = 1.0
    scaleY = 1.0
    paperColor = None

    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.pageWidth = 0.0
        self.pageHeight = 0.0
        self.computedRotation = Rotate_0

    def copy(self):
        """Return a copy of the page with the same instance attributes."""
        return copy.copy(self)

    def rect(self):
        """Return our QRect(), with position and size."""
        return QRect(self.x, self.y, self.width, self.height)

    def setPos(self, point):
        """Set our position (QPoint).

        Normally this is done by the layout in the updatePagePositions() method.

        """
        self.x = point.x()
        self.y = point.y()

    def pos(self):
        """Return our position (QPoint)."""
        return QPoint(self.x, self.y)

    def setSize(self, size):
        """Set our size (QSize).

        Normally this is done by the layout in the updateSizeFromLayout() method.

        """
        self.width = size.width()
        self.height = size.height()

    def size(self):
        """Return our size (QSize)."""
        return QSize(self.width, self.height)

    def setPageSize(self, sizef):
        """Set our natural page size (QSizeF).

        This value is only used in the computeSize() method, to get the size
        in pixels of the page.

        By the default implementation of computeSize(), the page size is assumed
        to be in points, 1/72 of an inch.

        """
        self.pageWidth = sizef.width()
        self.pageHeight = sizef.height()

    def pageSize(self):
        """Return our natural page size (QSizeF).

        This value is only used in the computeSize() method, to get the size
        in pixels of the page.

        By the default implementation of computeSize(), the page size is assumed
        to be in points, 1/72 of an inch.

        """
        return QSizeF(self.pageWidth, self.pageHeight)

    def computeSize(self, rotation, dpiX, dpiY, zoomFactor):
        """Return a tuple (w, h) representing the size of the page in pixels.

        This size is computed based on the page's natural size, its scale and
        the specified rotation, dpi, scale and zoomFactor.

        """
        w = self.pageWidth * self.scaleX
        h = self.pageHeight * self.scaleY
        if rotation & 1:
            w, h = h, w
        # now handle dpi, scale and zoom
        w = round(w * dpiX / 72.0 * zoomFactor)
        h = round(h * dpiY / 72.0 * zoomFactor)
        return w, h

    def zoomForWidth(self, width, rotation, dpiX):
        """Return the zoom we need to display ourselves at the given width."""
        if (self.rotation + rotation) & 1:
            w = self.pageHeight / self.scaleY
        else:
            w = self.pageWidth / self.scaleX
        return width * 72.0 / dpiX / w

    def zoomForHeight(self, height, rotation, dpiY):
        """Return the zoom we need to display ourselves at the given height."""
        if (self.rotation + rotation) & 1:
            h = self.pageWidth / self.scaleX
        else:
            h = self.pageHeight / self.scaleY
        return height * 72.0 / dpiY / h

    def paint(self, painter, rect, callback=None):
        """Reimplement this to paint our Page.

        The View calls this method in the paint event. If you can't paint
        quickly, just return and schedule an image to be rendered in the
        background. If a callback is specified, it is called when the image
        is ready with the page as argument.

        By default, this method calls the renderer's paint() method.

        """
        self.renderer and self.renderer.paint(self, painter, rect, callback)

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
    
    def area2page(self, rect, width=None, height=None):
        """Return a QRect, converting an original area to page coordinates.
        
        `rect` may be a QRect or QRectF instance. The `width` and `height`
        refer to the original (unrotated) width and height of the page's
        contents, and default to pageWidth and pageHeight.
        
        """
        if width  is None: width  = self.pageWidth
        if height is None: height = self.pageHeight
        rect = rect.normalized()
        left, top, right, bottom = rect.getCoords()
        # first scale to a 0-1 scale
        left   /= width
        top    /= height
        right  /= width
        bottom /= height
        # then rotate
        if self.computedRotation:
            left, top, right, bottom = rotate_rect_cw[self.computedRotation](left, top, right, bottom)
        # then scale to page coordinates
        rect = QRect()
        rect.setCoords(left   * self.width,
                       top    * self.height,
                       right  * self.width,
                       bottom * self.height)
        return rect
        
    def page2area(self, rect, width=None, height=None):
        """Return a QRectF(), converting a page rectangle to the original area.
        
        This is the opposite of area2page().
        
        The specified `rect` (QRect) should be in page coordinates, and is
        scaled into the specified width and height, and rotated so it
        corresponds with the original page rotation.
        
        This way, objects like links can be correctly found in a scaled and 
        rotated page. The returned QRectF() falls in the rect(0, 0, width,
        height) and both width and height default to pageWidth and pageHeight.
        
        """
        if width  is None: width  = self.pageWidth
        if height is None: height = self.pageHeight
        rect = rect.normalized()
        left, top, right, bottom = rect.getCoords()
        # first scale to a 0-1 scale
        left   /= self.width
        top    /= self.height
        right  /= self.width
        bottom /= self.height
        # then rotate backwards
        if self.computedRotation:
            left, top, right, bottom = rotate_rect_ccw[self.computedRotation](left, top, right, bottom)
        # then scale to the original coordinates
        rect = QRectF()
        rect.setCoords(left   * width,
                       top    * height,
                       right  * width,
                       bottom * height)
        return rect
    
    def area2point(self, x, y, width=None, height=None):
        """Return a tuple (x, y), converting a point on the original area to the page."""
        if width  is None: width  = self.pageWidth
        if height is None: height = self.pageHeight
        x /= width
        y /= height
        if self.computedRotation: x, y = rotate_cw[self.computedRotation](x, y)
        return x * self.width, y * self.height
    
    def point2area(self, x, y, width=None, height=None):
        """Return a tuple (x, y), converting a point on the page to the original area."""
        if width  is None: width  = self.pageWidth
        if height is None: height = self.pageHeight
        x /= self.width
        y /= self.height
        if self.computedRotation: x, y = rotate_ccw[self.computedRotation](x, y)
        return x * width, y * height
    
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
        """Return a list() of zero or more links touched by QPoint point.

        The point is in page coordinates.
        The list is sorted with the smallest rectangle first.

        """
        # Link objects have their area ranging
        # in width and height from 0.0 to 1.0 ...
        x, y = self.point2area(point.x(), point.y(), 1, 1)
        links = self.links()
        return sorted(links.at(x, y), key=links.width)

    def linksIn(self, rect):
        """Return an unordered set of links enclosed in rectangle.
        
        The rectangle is in page coordinates.
        
        """
        return self.links().inside(*self.page2area(rect, 1, 1).getCoords())

    def linkRect(self, link):
        """Return a QRect encompassing the linkArea of a link in coordinates of our page."""
        return self.area2page(link.area, 1, 1)



# rotation helper functions for a point....
def _rotate_90 (x, y): return 1-y, x
def _rotate_180(x, y): return 1-x, 1-y
def _rotate_270(x, y): return y, 1-x
    
rotate_cw =  { Rotate_90:  _rotate_90,
               Rotate_180: _rotate_180,
               Rotate_270: _rotate_270 }

rotate_ccw = { Rotate_90:  _rotate_270,
               Rotate_180: _rotate_180,
               Rotate_270: _rotate_90  }

# ... and for a rect
def _rotate_rect_90 (left, top, right, bottom): return 1-bottom, left, 1-top, right
def _rotate_rect_180(left, top, right, bottom): return 1-right, 1-bottom, 1-left, 1-top
def _rotate_rect_270(left, top, right, bottom): return 1-bottom, left, 1-top, right

rotate_rect_cw =  { Rotate_90:  _rotate_rect_90,
                    Rotate_180: _rotate_rect_180,
                    Rotate_270: _rotate_rect_270 }

rotate_rect_ccw = { Rotate_90:  _rotate_rect_270,
                    Rotate_180: _rotate_rect_180,
                    Rotate_270: _rotate_rect_90  }


