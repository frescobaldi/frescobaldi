# -*- coding: utf-8 -*-
#
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


import collections
import contextlib

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt
from PyQt5.QtGui import QBitmap, QMouseEvent, QRegion
from PyQt5.QtWidgets import QApplication


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

    """

    #: Whether to enable handling of long mouse presses; set to False to disable
    longMousePressEnabled = True

    #: Allow moving some pixels before a long mouse press is considered a drag
    longMousePressTolerance = 3

    #: How long to presse a mouse button (in msec) for a long press
    longMousePressTime = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._longPressTimer = None
        self._longPressAttrs = None
        self._longPressPos = None

    def _startLongMousePressEvent(self, ev):
        """Start the timer for a QMouseEvent mouse press event."""
        self._cancelLongMousePressEvent()
        self._longPressTimer = self.startTimer(self.longMousePressTime)
        # copy the event's attributes because Qt might reuse the event
        self._longPressAttrs = (ev.type(),
            ev.localPos(), ev.windowPos(), ev.screenPos(),
            ev.button(), ev.buttons(), ev.modifiers())
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
            self._longPressAttrs = None
            self._longPressPos = None

    def longMousePressEvent(self, ev):
        """Implement this to handle a long mouse press event."""
        pass

    def timerEvent(self, ev):
        """Implemented to check for a long mouse button press."""
        if ev.timerId() == self._longPressTimer:
            event = QMouseEvent(*self._longPressAttrs)
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
    """Rotate matrix inside a rectangular area of width x height.

    The ``matrix`` can be a either a QPainter or a QTransform. The ``rotation``
    is 0, 1, 2 or 3, etc. (``Rotate_0``, ``Rotate_90``, etc...). If ``dest`` is
    True, ``width`` and ``height`` refer to the destination, otherwise to the
    source.

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


def align(w, h, ow, oh, alignment=Qt.AlignCenter):
    """Return (x, y) to align a rect w x h in an outer rectangle ow x oh.

    The alignment can be a combination of the Qt.Alignment flags.
    If w > ow, x = -1; and if h > oh, y = -1.

    """
    if w > ow:
        x = -1
    elif alignment & Qt.AlignHCenter:
        x = (ow - w) // 2
    elif alignment & Qt.AlignRight:
        x = ow - w
    else:
        x = 0
    if h > oh:
        y = -1
    elif alignment & Qt.AlignVCenter:
        y = (oh - h) // 2
    elif alignment & Qt.AlignBottom:
        y = oh - h
    else:
        y = 0
    return x, y


def alignrect(rect, point, alignment=Qt.AlignCenter):
    """Align rect with point according to the alignment.

    The alignment can be a combination of the Qt.Alignment flags.

    """
    rect.moveCenter(point)
    if alignment & Qt.AlignLeft:
        rect.moveLeft(point.x())
    elif alignment & Qt.AlignRight:
        rect.moveRight(point.x())
    if alignment & Qt.AlignTop:
        rect.moveTop(point.y())
    elif alignment & Qt.AlignBottom:
        rect.moveBottom(point.y())


# Found at: https://stackoverflow.com/questions/1986152/why-doesnt-python-have-a-sign-function
def sign(x):
    """Return the sign of x: -1 if x < 0, 0 if x == 0, or 1 if x > 0."""
    return bool(x > 0) - bool(x < 0)


@contextlib.contextmanager
def signalsBlocked(*objs):
    """Block the pyqtSignals of the given QObjects during the context."""
    blocks = [obj.blockSignals(True) for obj in objs]
    try:
        yield
    finally:
        for obj, block in zip(objs, blocks):
            obj.blockSignals(block)


def autoCropRect(image):
    """Return a QRect specifying the contents of the QImage.

    Edges of the image are trimmed if they have the same color.

    """
    # pick the color at most of the corners
    colors = collections.defaultdict(int)
    w, h = image.width(), image.height()
    for x, y in (0, 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1):
        colors[image.pixel(x, y)] += 1
    most = max(colors, key=colors.get)
    # let Qt do the masking work
    mask = image.createMaskFromColor(most)
    return QRegion(QBitmap.fromImage(mask)).boundingRect()


def tempdir():
    """Return a temporary directory that is erased on app quit."""
    import tempfile
    global _tempdir
    try:
        _tempdir
    except NameError:
        name = QApplication.applicationName().translate({ord('/'): None}) or 'qpageview'
        _tempdir = tempfile.mkdtemp(prefix=name + '-')
        import atexit
        import shutil
        @atexit.register
        def remove():
            shutil.rmtree(_tempdir, ignore_errors=True)
    return tempfile.mkdtemp(dir=_tempdir)

