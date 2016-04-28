# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2016 by Wilbert Berendsen
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

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF


from .constants import *


class AbstractPage:
    def __init__(self):
        self._rect = QRect()
        self._pageSize = QSizeF()
        self._scale = QPointF(1.0, 1.0)
        self._layout = lambda: None
    
    def layout(self):
        """Return the Layout if we are part of one."""
        return self._layout()
    
    def rect(self):
        """Return our QRect(), with position and size."""
        return self._rect
    
    def size(self):
        """Return our size."""
        return self._rect.size()
    
    def height(self):
        """Return our height."""
        return self._rect.height()
        
    def width(self):
        """Return our width."""
        return self._rect.width()
        
    def pos(self):
        """Return our position."""
        return self._rect.topLeft()
    
    def setPos(self, point):
        """Set our position (affects the Layout)."""
        self._rect.moveTopLeft(point)
    
    def setSize(self, size):
        """Set our size (QSize)."""
        self._rect.setSize(size)

    def setScale(self, scale):
        """Change the display scale (QPointF)."""
        self._scale = scale
        
    def scale(self):
        """Return our display scale (QPointF)."""
        return self._scale
    
    def setPageSizeF(self, sizef):
        """Set our natural page size (QSizeF).
        
        This value is only used in the computeSize() method, to get the size
        in pixels of the page.
        
        By the default implementation of computeSize(), the page size is assumed
        to be in points, 1/72 of an inch.
        
        """
        self._pageSize = sizef
    
    def pageSizeF(self):
        """Return our natural page size (QSizeF).
        
        This value is only used in the computeSize() method, to get the size
        in pixels of the page.
        
        By the default implementation of computeSize(), the page size is assumed
        to be in points, 1/72 of an inch.
        
        """
        return self._pageSize()

    def computeSize(self, layout):
        """Compute and set the size() of the page.
        
        The default implementation takes into account the DPI of the layout,
        the scale of the layout and the scale of the page.
        
        """
        size = self.pageSizeF() * layout.dpi() / 72.0 * layout.scale() * self_.scale
        self.setSize(size)



