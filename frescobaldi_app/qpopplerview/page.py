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
    
    def setWidth(self, width):
        """Forces our width (influences size() and dpi())."""
        xdpi = self.layout().dpi()[0] if self.layout() else 72.0
        self.setScale(width * 72.0 / xdpi / self._pageSize.width())

    def setHeight(self, height):
        """Forces our height (influences size() and dpi())."""
        ydpi = self.layout().dpi()[1] if self.layout() else 72.0
        self.setScale(height * 72.0 / ydpi / self._pageSize.height())
        
    def paint(self, painter, rect):
        update_rect = rect & self.rect()
        if not update_rect:
            return
        image = cache.image(self._document, self._pageNumber, self.size())
        if image:
            image_rect = QRect(update_rect.topLeft() - self.rect().topLeft(), update_rect.size())
            painter.drawImage(update_rect, image, image_rect)
        else:
            painter.fillRect(update_rect, QApplication.palette().background().color())


        