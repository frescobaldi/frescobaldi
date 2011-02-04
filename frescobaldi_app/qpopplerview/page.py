# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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
A Page is resposible for drawing a page of a Poppler document
inside a layout.
"""

import popplerqt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import cache
from . import rectangles


class Page(object):
    def __init__(self, document, pageNumber):
        self._document = document
        self._pageNumber = pageNumber
        self._pageSize = document.page(pageNumber).pageSize()
        self._rotation = popplerqt4.Poppler.Page.Rotate0
        self._rect = QRect()
        self._scale = 1.0
        self._layout = lambda: None
        
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
        """Returns the scale we need to display ourselves at the given width."""
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
        image = cache.image(self)
        if image:
            painter.drawImage(update_rect, image, image_rect)
        else:
            # schedule an image to be generated, if done our update() method is called
            cache.generate(self)
            # find suitable image to be scaled from other size
            image = cache.image(self, False)
            if image:
                hscale = float(image.width()) / self.width()
                vscale = float(image.height()) / self.height()
                image_rect = QRectF(image_rect.x() * hscale, image_rect.y() * vscale,
                                    image_rect.width() * hscale, image_rect.height() * vscale)
                painter.drawImage(QRectF(update_rect), image, image_rect)
            else:
                # draw blank paper
                painter.fillRect(update_rect, self.document().paperColor())

    def update(self):
        """Called when an image is drawn."""
        if self.layout():
            self.layout().updatePage(self)
            
    def _links(self):
        """(Internal) Returns a position-searchable list of the links in the page."""
        try:
            return self._link_rectangles
        except AttributeError:
            res = self._link_rectangles = rectangles.Rectangles(
                self.document().page(self.pageNumber()).links(),
                lambda link: link.linkArea().normalized().getCoords())
            return res
    
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
            if self._rotation == popplerqt4.Poppler.Page.Rotate90:
                x, y = y, 1-x
            elif self._rotation == popplerqt4.Poppler.Page.Rotate180:
                x, y = 1-x, 1-y
            else: # 270
                x, y = 1-y, x
        return list(sorted(self._links().at(x, y), key=lambda link: link.linkArea().width()))
        
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
            if self._rotation == popplerqt4.Poppler.Page.Rotate90:
                left, top, right, bottom = top, 1-right, bottom, 1-left
            elif self._rotation == popplerqt4.Poppler.Page.Rotate180:
                left, top, right, bottom = 1-right, 1-bottom, 1-left, 1-top
            else: # 270
                left, top, right, bottom = 1-bottom, left, 1-top, right
        return self._links().inside(left, top, right, bottom)

    def linkRect(self, link):
        """Returns a QRect encompassing the linkArea() of the link in coordinates of our rect()."""
        left, top, right, bottom = link.linkArea().normalized().getCoords()
        # rotate
        if self._rotation:
            if self._rotation == popplerqt4.Poppler.Page.Rotate90:
                left, top, right, bottom = 1-bottom, left, 1-top, right
            elif self._rotation == popplerqt4.Poppler.Page.Rotate180:
                left, top, right, bottom = 1-right, 1-bottom, 1-left, 1-top
            else: # 270
                left, top, right, bottom = top, 1-right, bottom, 1-left
        rect = QRect()
        rect.setCoords(left * self.width(), top * self.height(), right * self.width(), bottom * self.height())
        rect.translate(self.pos())
        return rect
        
