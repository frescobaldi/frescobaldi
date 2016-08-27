# This file is part of the qpopplerview package.
#
# Copyright (c) 2010 - 2014 by Wilbert Berendsen
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
A Page is responsible for drawing a page of a Poppler document
inside a layout.
"""

try:
    import popplerqt5
except ImportError:
    from . import popplerqt5_dummy as popplerqt5

from PyQt5.QtCore import QRect, QRectF, QSize

from . import cache
from .locking import lock


class Page(object):
    """Represents a page from a Poppler.Document.
    
    It maintains its own size and can draw itself using the cache.
    It also can maintain a list of links and return links at certain
    points or rectangles.
    
    The visible attribute (setVisible and visible) defaults to True but
    can be set to False to hide the page from a Surface (this is done by
    the Layout).
    
    """
    def __init__(self, document, pageNumber):
        self._document = document
        self._pageNumber = pageNumber
        self._pageSize = document.page(pageNumber).pageSize()
        self._rotation = popplerqt5.Poppler.Page.Rotate0
        self._rect = QRect()
        self._scale = 1.0
        self._visible = True
        self._layout = lambda: None
        self._waiting = True # whether image still needs to be generated
        self._retinaFactor = 1 # Is updated when painted
        
    def document(self):
        """Returns the document."""
        return self._document
        
    def pageNumber(self):
        """Returns the page number."""
        return self._pageNumber
    
    def pageSize(self):
        """The page size in points (1/72 inch), taking rotation into account."""
        return self._pageSize
        
    def layout(self):
        """Returns the Layout if we are part of one."""
        return self._layout()
    
    def visible(self):
        """Returns True if this page is visible (will be displayed)."""
        return self._visible
        
    def setVisible(self, visible):
        """Sets whether  this page is visible (will be displayed)."""
        self._visible = visible
        
    def rect(self):
        """Returns our QRect(), with position and size."""
        return self._rect
    
    def size(self):
        """Returns our size."""
        return self._rect.size()
    
    def height(self):
        """Returns our height."""
        return self._rect.height()
        
    def width(self):
        """Returns our width."""
        return self._rect.width()
        
    def physWidth(self):
        """Returns the width that the image should have."""
        return self.width()*self._retinaFactor

    def physHeight(self):
        """Returns the height that the image should have."""
        return self.height()*self._retinaFactor

    def pos(self):
        """Returns our position."""
        return self._rect.topLeft()
    
    def setPos(self, point):
        """Sets our position (affects the Layout)."""
        self._rect.moveTopLeft(point)
    
    def setRotation(self, rotation):
        """Sets our Poppler.Page.Rotation."""
        old, self._rotation = self._rotation, rotation
        if (old ^ rotation) & 1:
            self._pageSize.transpose()
            self.computeSize()
    
    def rotation(self):
        """Returns our rotation."""
        return self._rotation
    
    def computeSize(self):
        """Recomputes our size."""
        xdpi, ydpi = self.layout().dpi() if self.layout() else (72.0, 72.0)
        x = round(self._pageSize.width() * xdpi / 72.0 * self._scale)
        y = round(self._pageSize.height() * ydpi / 72.0 * self._scale)
        self._rect.setSize(QSize(x, y))
        
    def setScale(self, scale):
        """Changes the display scale."""
        self._scale = scale
        self.computeSize()
        
    def scale(self):
        """Returns our display scale."""
        return self._scale
    
    def scaleForWidth(self, width):
        """Returns the scale we need to display ourselves at the given width."""
        if self.layout():
            return width * 72.0 / self.layout().dpi()[0] / self._pageSize.width()
        else:
            return float(width) / self._pageSize.width()
        
    def scaleForHeight(self, height):
        """Returns the scale we need to display ourselves at the given height."""
        if self.layout():
            return height * 72.0 / self.layout().dpi()[1] / self._pageSize.height()
        else:
            return float(height) / self._pageSize.height()
        
    def setWidth(self, width):
        """Change our scale to force our width to the given value."""
        self.setScale(self.scaleForWidth(width))

    def setHeight(self, height):
        """Change our scale to force our height to the given value."""
        self.setScale(self.scaleForHeight(height))
    
    def paint(self, painter, rect):
        update_rect = rect & self.rect()
        if not update_rect:
            return
        image_rect = QRect(update_rect.topLeft() - self.rect().topLeft(), update_rect.size())
        # Update retinaFactor
        self._retinaFactor = max(painter.device().devicePixelRatio(),self._retinaFactor);
        # image_rect *= _retinaFactor
        image_rect.moveTopLeft( image_rect.topLeft()*self._retinaFactor );
        image_rect.setSize( image_rect.size()*self._retinaFactor );

        image = cache.image(self)
        self._waiting = not image
        if image:
            painter.drawImage(update_rect, image, image_rect)
        else:
            # schedule an image to be generated, if done our update() method is called
            cache.generate(self)
            # find suitable image to be scaled from other size
            image = cache.image(self, False)
            if image:
                hscale = float(image.width()) / self.physWidth()
                vscale = float(image.height()) / self.physHeight()
                image_rect = QRectF(image_rect.x() * hscale, image_rect.y() * vscale,
                                    image_rect.width() * hscale, image_rect.height() * vscale)
                painter.drawImage(QRectF(update_rect), image, image_rect)
            else:
                # draw blank paper, using the background color of the cache rendering (if set)
                # or from the document itself.
                color = (cache.options(self.document()).paperColor()
                         or cache.options().paperColor() or self.document().paperColor())
                painter.fillRect(update_rect, color)

    def update(self):
        """Called when an image is drawn."""
        # only redraw when we were waiting for a correctly sized image.
        if self._waiting and self.layout():
            self.layout().updatePage(self)
    
    def repaint(self):
        """Call this to force a repaint (e.g. when the rendering options are changed)."""
        self._waiting = True
        cache.generate(self)
    
    def image(self, rect, xdpi=72.0, ydpi=None, options=None):
        """Returns a QImage of the specified rectangle (relative to our top-left position).
        
        xdpi defaults to 72.0 and ydpi defaults to xdpi.
        options may be a render.RenderOptions instance that will set some document
        rendering options just before rendering the image.
        """
        if ydpi is None:
            ydpi = xdpi
        hscale = (xdpi * self.pageSize().width()) / (72.0 * self.width())
        vscale = (ydpi * self.pageSize().height()) / (72.0 * self.height())
        x = rect.x() * hscale
        y = rect.y() * vscale
        w = rect.width() * hscale
        h = rect.height() * vscale
        with lock(self.document()):
            options and options.write(self.document())
            page = self.document().page(self._pageNumber)
            image = page.renderToImage(xdpi, ydpi, x, y, w, h, self._rotation)
        image.setDotsPerMeterX(int(xdpi * 39.37))
        image.setDotsPerMeterY(int(ydpi * 39.37))
        return image
    
    def linksAt(self, point):
        """Returns a list() of zero or more links touched by point (relative to surface).
        
        The list is sorted with the smallest rectangle first.
        
        """
        # Poppler.Link objects have their linkArea() ranging in width and height
        # from 0.0 to 1.0, so divide by resp. height and width of the Page.
        point = point - self.pos()
        x = float(point.x()) / self.width()
        y = float(point.y()) / self.height()
        # rotate
        if self._rotation:
            if self._rotation == popplerqt5.Poppler.Page.Rotate90:
                x, y = y, 1-x
            elif self._rotation == popplerqt5.Poppler.Page.Rotate180:
                x, y = 1-x, 1-y
            else: # 270
                x, y = 1-y, x
        return list(sorted(cache.links(self).at(x, y), key=lambda link: link.linkArea().width()))
        
    def linksIn(self, rect):
        """Returns an unordered set() of links enclosed in rectangle (relative to surface)."""
        rect = rect.normalized()
        rect.translate(-self.pos())
        left   = float(rect.left())   / self.width()
        top    = float(rect.top())    / self.height()
        right  = float(rect.right())  / self.width()
        bottom = float(rect.bottom()) / self.height()
        # rotate
        if self._rotation:
            if self._rotation == popplerqt5.Poppler.Page.Rotate90:
                left, top, right, bottom = top, 1-right, bottom, 1-left
            elif self._rotation == popplerqt5.Poppler.Page.Rotate180:
                left, top, right, bottom = 1-right, 1-bottom, 1-left, 1-top
            else: # 270
                left, top, right, bottom = 1-bottom, left, 1-top, right
        return cache.links(self).inside(left, top, right, bottom)

    def linkRect(self, linkarea):
        """Returns a QRect encompassing the linkArea (of a link) in coordinates of our rect()."""
        left, top, right, bottom = linkarea.normalized().getCoords()
        # rotate
        if self._rotation:
            if self._rotation == popplerqt5.Poppler.Page.Rotate90:
                left, top, right, bottom = 1-bottom, left, 1-top, right
            elif self._rotation == popplerqt5.Poppler.Page.Rotate180:
                left, top, right, bottom = 1-right, 1-bottom, 1-left, 1-top
            else: # 270
                left, top, right, bottom = top, 1-right, bottom, 1-left
        rect = QRect()
        rect.setCoords(left * self.width(), top * self.height(), right * self.width(), bottom * self.height())
        rect.translate(self.pos())
        return rect
        
    def text(self, rect):
        """Returns text inside rectangle (relative to surface)."""
        rect = rect.normalized()
        rect.translate(-self.pos())
        w, h = self.pageSize().width(), self.pageSize().height()
        left   = float(rect.left())   / self.width()  * w
        top    = float(rect.top())    / self.height() * h
        right  = float(rect.right())  / self.width()  * w
        bottom = float(rect.bottom()) / self.height() * h
        if self._rotation:
            if self._rotation == popplerqt5.Poppler.Page.Rotate90:
                left, top, right, bottom = top, w-right, bottom, w-left
            elif self._rotation == popplerqt5.Poppler.Page.Rotate180:
                left, top, right, bottom = w-right, h-bottom, w-left, h-top
            else: # 270
                left, top, right, bottom = h-bottom, left, h-top, right
        rect = QRectF()
        rect.setCoords(left, top, right, bottom)
        with lock(self.document()):
            page = self.document().page(self._pageNumber)
            return page.text(rect)
        
    def searchRect(self, rectF):
        """Returns a QRect encompassing the given rect (in points) to our position, size and rotation."""
        rect = rectF.normalized()
        left, top, right, bottom = rect.getCoords()
        w, h = self.pageSize().width(), self.pageSize().height()
        hscale = self.width()  / float(w)
        vscale = self.height() / float(h)
        if self._rotation:
            if self._rotation == popplerqt5.Poppler.Page.Rotate90:
                left, top, right, bottom = w-bottom, left, w-top, right
            elif self._rotation == popplerqt5.Poppler.Page.Rotate180:
                left, top, right, bottom = w-right, h-bottom, w-left, h-top
            else: # 270
                left, top, right, bottom = top, h-right, bottom, h-left
        rect = QRect()
        rect.setCoords(left * hscale, top * vscale, right * hscale, bottom * vscale)
        return rect
        
