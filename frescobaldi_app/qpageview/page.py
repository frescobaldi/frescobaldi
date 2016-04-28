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


from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)


class AbstractPage:
    def __init__(self):
        self._rect = QRect()
        self._pageSize = QSizeF()
        self._scale = QPointF(1.0, 1.0)
        self._rotation = Rotate_0
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
        """Set our scale (QPointF). 
        
        Normally you'd leave the scale at QPointF(1.0, 1.0), but you can use
        it to support pages with non-square pixels, etc.
        
        In all size computations, the scaling is applied *before* the rotation.
        
        """
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
        return self._pageSize

    def setRotation(self, rotation):
        """Set the rotation (see .constants) of this page."""
        self._rotation = rotation
    
    def rotation(self):
        """Return the rotation of this page."""
        return self._rotation
    
    def computeSize(self, layout):
        """Compute and set the size() of the page.
        
        The default implementation takes into account our pageSizeF(), scale 
        and rotation, and then the rotation, scale, DPI and zoom factor of 
        the layout.
        
        """
        # our size
        w = self._pageSize.width() * self._scale.x()
        h = self._pageSize.height() * self._scale.y()
        # handle ours and the layout's rotation in one go
        if (self._rotation + layout.rotation()) & 1:
            w, h = h, w
        # now handle the layout's scale, dpi and zoom
        w = w * layout.dpi().x() / 72.0 * layout.scale().x() * layout.zoomFactor()
        h = h * layout.dpi().y() / 72.0 * layout.scale().y() * layout.zoomFactor()
        self.setSize(QSize(w, h))

    def zoomForWidth(self, layout, width):
        """Return the zoom we need to display ourselves at the given width."""
        if (self._rotation + layout.rotation()) & 1:
            w = self._pageSize.height() / self._scale.y()
        else:
            w = self._pageSize.width() / self._scale.x()
        return width * 72.0 / layout.dpi().x() / w / layout.scale().x()
        
    def zoomForHeight(self, layout, height):
        """Return the zoom we need to display ourselves at the given height."""
        if (self._rotation + layout.rotation()) & 1:
            h = self._pageSize.width() / self._scale.x()
        else:
            h = self._pageSize.height() / self._scale.y()
        return height * 72.0 / layout.dpi().y() / h / layout.scale().y()



