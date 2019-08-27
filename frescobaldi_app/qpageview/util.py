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
Small utilities and simple base classes for the qpageview module.
"""


from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize

from .constants import (
    Rotate_90,
    Rotate_180,
    Rotate_270,
)


class Rectangular:
    """Defines a Qt-inspired and -based interface for rectangular objects.

    The attributes x, y, width and height default to 0 at the class level
    and can be set and read directly.

    For convenience, Qt-styled methods are available to access and modify these
    attributes.

    """
    x = 0
    y = 0
    width = 0
    height = 0

    def setPos(self, point):
        """Set the x and y coordinates from the given QPoint point."""
        self.x = point.x()
        self.y = point.y()

    def pos(self):
        """Return our x and y coordinates as a QPoint(x, y)."""
        return QPoint(self.x, self.y)

    def setSize(self, size):
        """Set the height and width attributes from the given QSize size."""
        self.width = size.width()
        self.height = size.height()

    def size(self):
        """Return the height and width attributes as a QSize(width, height)."""
        return QSize(self.width, self.height)

    def setGeometry(self, rect):
        """Set our x, y, width and height directly from the given QRect."""
        self.x, self.y, self.width, self.height = rect.getRect()

    def geometry(self):
        """Return our x, y, width and height as a QRect."""
        return QRect(self.x, self.y, self.width, self.height)

    def rect(self):
        """Return QRect(0, 0, width, height)."""
        return QRect(0, 0, self.width, self.height)


class MapToPage:
    """Simple class wrapping a QTransform to map rect and point to page coordinates."""
    def __init__(self, transform):
        self.t = transform
    
    def rect(self, rect):
        """Convert QRect or QRectF to a QRect in page coordinates."""
        return self.t.mapRect(QRectF(rect)).toRect()
    
    def point(self, point):
        """Convert QPointF or QPoint to a QPoint in page coordinates."""
        return self.t.map(QPointF(point)).toPoint()


class MapFromPage(MapToPage):
    """Simple class wrapping a QTransform to map rect and point from page to original coordinates."""
    def rect(self, rect):
        """Convert QRect or QRectF to a QRectF in original coordinates."""
        return self.t.mapRect(QRectF(rect))
    
    def point(self, point):
        """Convert QPointF or QPoint to a QPointF in original coordinates."""
        return self.t.map(QPointF(point))



# Found at: https://stackoverflow.com/questions/1986152/why-doesnt-python-have-a-sign-function
def sign(x):
    """Return the sign of x: -1 if x < 0, 0 if x == 0, or 1 if x > 0."""
    return bool(x > 0) - bool(x < 0)


