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

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PyQt5.QtGui import QColor

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)


class AbstractPage:
    
    # the renderer can take care of rendering images in the background
    renderer = None
    
    def __init__(self, renderer=None):
        self._rect = QRect()
        self._pageSize = QSizeF()
        self._scale = QPointF(1.0, 1.0)
        self._rotation = Rotate_0
        self._computedRotation = Rotate_0
        if renderer is not None:
            self.renderer = renderer
    
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
    
    def computedRotation(self):
        """Return the real rotation used for this Page.
        
        This means our rotation added to the layout's rotation.
        This value is set by the computeSize() method and used by the paint()
        method.
        
        """
        return self._computedRotation
    
    def updateSizeFromLayout(self, layout):
        """Compute and set the size() of the page.
        
        This method is called on layout update by the updatePageSizes method.
        The default implementation takes into account our pageSizeF(), scale 
        and rotation, and then the rotation, scale, DPI and zoom factor of 
        the layout. It uses the computeSize() method to perform the calculation.
        
        """
        self._computedRotation = rotation = (self._rotation + layout.rotation()) & 3
        self.setSize(QSize(*self.computeSize(
            rotation, layout.dpi(), layout.scale(), layout.zoomFactor())))
    
    def computeSize(self, rotation, dpi, scale, zoomFactor):
        """Return a tuple (w, h) representing the size of the page in pixels.
        
        This size is computed based on the page's natural size, its scale and
        the specified rotation, dpi, scale and zoomFactor.
        
        """
        w = self._pageSize.width() * self._scale.x()
        h = self._pageSize.height() * self._scale.y()
        if rotation & 1:
            w, h = h, w
        # now handle dpi, scale and zoom
        w = w * dpi.x() / 72.0 * scale.x() * zoomFactor
        h = h * dpi.y() / 72.0 * scale.y() * zoomFactor
        return w, h

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
    
    def paint(self, painter, dest_rect, source_rect):
        """Reimplement this to paint our Page.
        
        The View calls this method in the paint event. If it returns a non-true 
        value, it is assumed that the painting would take too much time and 
        that nothing or an intermediate image is painted.
        
        In that case, the View calls redraw(). It is expected that the page will
        initiate a rendering job in the background and call
        View.notifyPageRedraw when the job has finished.
        
        The default implementation of this method simply draws a white square
        and returns True.
        
        """
        painter.fillRect(dest_rect, QColor(Qt.white))
        return True

    def redraw(self, view):
        """Should perform a redrawing job in the background.
        
        This method is called by the View in the paint event, when paint() did
        return a non-True value. If you didn't do it already, start a background
        job that renders the page.
        When the job is done, call view.notifyPageRedraw(page), and the View
        will request a paint update.
        
        The default implementation of this method calls
        redraw(self, view.notifyRedrawPage) on the renderer, which must be
        present in the renderer attribute.
        
        """
        self.renderer.redraw(self, view.notifyRedrawPage)

