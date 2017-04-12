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

    def updateSizeFromLayout(self, layout):
        """Compute and set the size() of the page.

        This method is called on layout update by the updatePageSizes method.
        The default implementation takes into account our pageSizeF(), scale
        and rotation, and then the rotation, scale, DPI and zoom factor of
        the layout. It uses the computeSize() method to perform the calculation.

        """
        self.computedRotation = rotation = (self.rotation + layout.rotation) & 3
        self.width, self.height = self.computeSize(
            rotation, layout.dpiX, layout.dpiY, layout.zoomFactor)

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

    def zoomForWidth(self, layout, width):
        """Return the zoom we need to display ourselves at the given width."""
        if (self.rotation + layout.rotation) & 1:
            w = self.pageHeight / self.scaleY
        else:
            w = self.pageWidth / self.scaleX
        return width * 72.0 / layout.dpiX / w

    def zoomForHeight(self, layout, height):
        """Return the zoom we need to display ourselves at the given height."""
        if (self.rotation + layout.rotation) & 1:
            h = self.pageWidth / self.scaleX
        else:
            h = self.pageHeight / self.scaleY
        return height * 72.0 / layout.dpiY / h

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

