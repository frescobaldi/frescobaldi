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
    """A Page is a rectangle that is positioned in a PageLayout.
    
    A Page has instance attributes...
    
    ...that normally do not change:
    
        `data`          object(s) that are understood by the renderer to render
        `pageWidth`     the original width in points (1/72 inch)
        `pageHeight`    the original height in points (1/72 inch)
    
    ... that can be modified by the user (having defaults at the class level):
    
        `rotation`      the rotation (Rotate_0)
        `scaleX`        the scale in X-direction (1.0)
        `scaleY`        the scale in Y-direction (1.0)
        
    ... and that are set by the layout when computing the size and positioning
        the pages:
    
        `x`             the position x-coordinate
        `y`             the position y-coordinate
        `width`         the width in pixels
        `height`        the height in pixels
        `computedRotation` the rotation in which finally to render
        
    """
    
    rotation = Rotate_0
    scaleX = 1.0
    scaleY = 1.0
    
    
    # the renderer can take care of rendering images in the background
    renderer = None
    
    def __init__(self, renderer=None):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.pageWidth = 0.0
        self.pageHeight = 0.0
        self.computedRotation = Rotate_0
        
        if renderer is not None:
            self.renderer = renderer
    
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
        """Return our position."""
        return QPoint(self.x, self.y)
    
    def setSize(self, size):
        """Set our size (QSize).
        
        Normally this is done by the layout in the updateSizeFromLayout() method.
        
        """
        self.width = size.width()
        self.height = size.height()

    def size(self):
        """Return our size (QSize)"""
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
    
    def updateSizeFromLayout(self, layout):
        """Compute and set the size() of the page.
        
        This method is called on layout update by the updatePageSizes method.
        The default implementation takes into account our pageSizeF(), scale 
        and rotation, and then the rotation, scale, DPI and zoom factor of 
        the layout. It uses the computeSize() method to perform the calculation.
        
        """
        self.computedRotation = rotation = (self.rotation + layout.rotation()) & 3
        self.width, self.height = self.computeSize(
            rotation, layout.dpi(), layout.scale(), layout.zoomFactor())
    
    def computeSize(self, rotation, dpi, scale, zoomFactor):
        """Return a tuple (w, h) representing the size of the page in pixels.
        
        This size is computed based on the page's natural size, its scale and
        the specified rotation, dpi, scale and zoomFactor.
        
        """
        w = self.pageWidth * self.scaleX
        h = self.pageHeight * self.scaleY
        if rotation & 1:
            w, h = h, w
        # now handle dpi, scale and zoom
        w = w * dpi.x() / 72.0 * scale.x() * zoomFactor
        h = h * dpi.y() / 72.0 * scale.y() * zoomFactor
        return w, h

    def zoomForWidth(self, layout, width):
        """Return the zoom we need to display ourselves at the given width."""
        if (self.rotation + layout.rotation()) & 1:
            w = self.pageHeight / self.scaleY
        else:
            w = self.pageWidth / self.scaleX
        return width * 72.0 / layout.dpi().x() / w / layout.scale().x()
        
    def zoomForHeight(self, layout, height):
        """Return the zoom we need to display ourselves at the given height."""
        if (self.rotation + layout.rotation()) & 1:
            h = self.pageWidth / self.scaleX
        else:
            h = self.pageHeight / self.scaleY
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

