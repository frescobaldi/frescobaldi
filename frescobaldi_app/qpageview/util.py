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


class LongMousePressMixin:
    """Mixin class to add support for long mouse press to a QWidget.

    To handle a long mouse press event, implement longMousePressEvent().

    The following instance variables can be altered:

    longMousePressEnabled = True    # set to False to disable
    longMousePressTolerance = 3     # number of pixels moving allowed
    longMousePressTime = 800        # msec a mouse press is considered long

    """

    longMousePressEnabled = True    # set to False to disable
    longMousePressTolerance = 3     # number of pixels moving allowed
    longMousePressTime = 800        # msec a mouse press is considered long

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._longPressTimer = None
        self._longPressEvent = None
        self._longPressPos = None

    def _startLongMousePressEvent(self, ev):
        """Start the timer for a QMouseEvent mouse press event."""
        self._cancelLongMousePressEvent()
        self._longPressTimer = self.startTimer(self.longMousePressTime)
        # copy the pos because Qt might reuse the event
        self._longPressEvent = ev
        self._longPressPos = ev.pos()

    def _checkLongMousePressEvent(self, ev):
        """Cancel the press event if the current event has moved more than 3 pixels."""
        if self._longPressTimer is not None:
            dist = (self._longPressPos - ev.pos()).manhattanLength()
            if dist > self.longMousePressTolerance:
                self._cancelLongMousePressEvent()

    def _cancelLongMousePressEvent(self):
        """Stop the timer for a long mouse press event."""
        if self._longPressTimer is not None:
            self.killTimer(self._longPressTimer)
            self._longPressTimer = None
            self._longPressEvent = None
            self._longPressPos = None

    def longMousePressEvent(self, ev):
        """Implement this to handle a long mouse press event."""
        pass

    def timerEvent(self, ev):
        """Implemented to check for a long mouse button press."""
        if ev.timerId() == self._longPressTimer:
            event = self._longPressEvent
            self._cancelLongMousePressEvent()
            self.longMousePressEvent(event)
        super().timerEvent(ev)

    def mousePressEvent(self, ev):
        """Reimplemented to check for a long mouse button press."""
        if self.longMousePressEnabled:
            self._startLongMousePressEvent(ev)
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        """Reimplemented to check for moves during a long press."""
        self._checkLongMousePressEvent(ev)
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        """Reimplemented to cancel a long press."""
        self._cancelLongMousePressEvent()
        super().mouseReleaseEvent(ev)


def rotate(matrix, rotation, width, height, dest=False):
    """Rotates matrix inside a rectangular area of width x height.

    The matrix can be a QPainter or a QTransform.
    Rotation is 0, 1, 2 or 3, etc. (Rotate_0, Rotate_90, etc...).
    If dest is True, width and height refer to the destination, otherwise
    to the source.

    """
    if rotation & 3:
        if dest or not rotation & 1:
            matrix.translate(width / 2, height / 2)
        else:
            matrix.translate(height / 2, width / 2)
        matrix.rotate(rotation * 90)
        if not dest or not rotation & 1:
            matrix.translate(width / -2, height / -2)
        else:
            matrix.translate(height / -2, width / -2)


# Found at: https://stackoverflow.com/questions/1986152/why-doesnt-python-have-a-sign-function
def sign(x):
    """Return the sign of x: -1 if x < 0, 0 if x == 0, or 1 if x > 0."""
    return bool(x > 0) - bool(x < 0)


