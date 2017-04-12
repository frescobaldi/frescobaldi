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
ScrollArea, that supports kinetic scrolling and other features.
"""

import math

from PyQt5.QtCore import QBasicTimer, QPoint, Qt
from PyQt5.QtWidgets import QAbstractScrollArea


class ScrollArea(QAbstractScrollArea):
    """A scroll area that supports kinetic scrolling and other features.

    Instance attributes:

        kineticscrolling (True): whether the wheel and pgup/pgdn keys etc use
                                 kinetic scrolling

        scrollupdatespersec (50): how many scroll updates to draw per second
                                 (50 is recommended).

    """

    kineticscrolling = True
    scrollupdatespersec = 50

    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._scroller = None
        self._scrollTimer = QBasicTimer()

    def wheelEvent(self, ev):
        if self.kineticscrolling:
            self.kineticAddDelta(-ev.angleDelta())
        else:
            super().wheelEvent(ev)

    def keyPressEvent(self, ev):
        """Kinetic cursor movements."""
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()
        # add Home and End, even in non-kinetic mode
        scroll = self.kineticScrollBy if self.kineticscrolling else self.scrollBy
        if ev.key() == Qt.Key_Home:
            scroll(QPoint(0, -vbar.value()))
        elif ev.key() == Qt.Key_End:
            scroll(QPoint(0, vbar.maximum() - vbar.value()))
        elif self.kineticscrolling:
            # make arrow keys and PgUp and PgDn kinetic
            if ev.key() == Qt.Key_PageDown:
                self.kineticAddDelta(QPoint(0, vbar.pageStep()))
            elif ev.key() == Qt.Key_PageUp:
                self.kineticAddDelta(QPoint(0, -vbar.pageStep()))
            elif ev.key() == Qt.Key_Down:
                self.kineticAddDelta(QPoint(0, vbar.singleStep()))
            elif ev.key() == Qt.Key_Up:
                self.kineticAddDelta(QPoint(0, -vbar.singleStep()))
            elif ev.key() == Qt.Key_Left:
                self.kineticAddDelta(QPoint(-hbar.singleStep(), 0))
            elif ev.key() == Qt.Key_Right:
                self.kineticAddDelta(QPoint(hbar.singleStep(), 0))
            else:
                super().keyPressEvent(ev)
        else:
            super().keyPressEvent(ev)

    def scrollOffset(self):
        """Return the current scroll offset."""
        x = self.horizontalScrollBar().value()
        y = self.verticalScrollBar().value()
        return QPoint(x, y)

    def canScrollBy(self, diff):
        """Does not scroll, but return the actual distance the View would scroll.

        diff is a QPoint instance.

        """
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()

        x = min(max(0, hbar.value() + diff.x()), hbar.maximum())
        y = min(max(0, vbar.value() + diff.y()), vbar.maximum())
        return QPoint(x - hbar.value(), y - vbar.value())

    def scrollForDragging(self, pos):
        """Slowly scroll the View if pos is close to the edge of the viewport.

        Can be used while dragging things.

        """
        viewport = self.viewport().rect()
        dx = pos.x() - viewport.left() - 12
        if dx >= 0:
            dx = max(0, pos.x() - viewport.right() + 12)
        dy = pos.y() - viewport.top() - 12
        if dy >= 0:
            dy = max(0, pos.y() - viewport.bottom() + 12)
        self.steadyScroll(QPoint(dx*10, dy*10))

    def scrollTo(self, pos):
        """Scroll the View to get pos (QPoint) in the top left corner (if possible).

        Returns the actual distance moved.

        """
        return self.scrollBy(pos - self.scrollOffset())

    def scrollBy(self, diff):
        """Scroll the View diff pixels (QPoint) in x and y direction.

        Returns the actual distance moved.

        """
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()
        x = hbar.value()
        hbar.setValue(hbar.value() + diff.x())
        x = hbar.value() - x
        y = vbar.value()
        vbar.setValue(vbar.value() + diff.y())
        y = vbar.value() - y
        return QPoint(x, y)

    def kineticScrollTo(self, pos):
        """Scroll the View to get pos (QPoint) in the top left corner (if possible).

        Returns the actual distance the scroll area will move.

        """
        return self.kineticScrollBy(pos - self.scrollOffset())

    def kineticScrollBy(self, diff):
        """Scroll the View diff pixels (QPoint) in x and y direction.

        Returns the actual distance the scroll area will move.

        """
        ret = self.canScrollBy(diff)
        if diff:
            scroller = KineticScroller()
            scroller.scrollBy(diff)
            self.startScrolling(scroller)
        return ret

    def kineticAddDelta(self, diff):
        """Add diff (QPoint) to an existing kinetic scroll.

        If no scroll is active, a new one is started (like kineticScrollBy).

        """
        if isinstance(self._scroller, KineticScroller):
            self._scroller.scrollBy(self._scroller.remainingDistance() + diff)
        else:
            self.kineticScrollBy(diff)

    def steadyScroll(self, diff):
        """Start steadily scrolling diff (QPoint) pixels per second.

        Stops automatically when the end is reached.

        """
        if diff:
            self.startScrolling(SteadyScroller(diff, self.scrollupdatespersec))
        else:
            self.stopScrolling()

    def startScrolling(self, scroller):
        """Begin a scrolling operation using the specified scroller."""
        self._scroller = scroller
        if not self._scrollTimer.isActive():
            self._scrollTimer.start(1000 / self.scrollupdatespersec, self)

    def stopScrolling(self):
        """Stop scrolling."""
        if self._scroller:
            self._scrollTimer.stop()
            self._scroller = None

    def isScrolling(self):
        """Return True if a scrolling movement is active."""
        return bool(self._scroller)

    def timerEvent(self, ev):
        """Called by the _scrollTimer."""
        diff = self._scroller.step()
        # when scrolling slowly, it might be that no redraw is needed
        if diff:
            # change the scrollbars, but check how far they really moved.
            if not self.scrollBy(diff) or self._scroller.finished():
                self.stopScrolling()


class Scroller:
    """Abstract base class, encapsulates scrolling behaviour.

    A Scroller subclass must implement the step() and finished() methods and
    may define additional methods.

    """
    def step(self):
        """Implement this method to return a QPoint for the current scrolling step."""

    def finished(self):
        """Implement this method to return True if scrolling is finished."""


class SteadyScroller(Scroller):
    """Scrolls the area steadily n pixels per second."""
    def __init__(self, speed, updates_per_second):
        """Initializes with speed (QPoint) pixels per second."""
        self._x = speed.x()
        self._y = speed.y()
        self._restx = 0
        self._resty = 0
        self._ups = updates_per_second

    def step(self):
        """Return a QPoint indicating the diff to scroll in this step.

        If this is a QPoint(0, 0) it does not indicate that scrolling has
        finished. Use finished() for that.

        """
        # the amount of pixels to scroll per second
        x = self._x
        y = self._y

        # how many updates per second, compute the number of pixes to scroll now
        ups = self._ups
        dx, rx = divmod(abs(x), ups)
        dy, ry = divmod(abs(y), ups)
        dx1, self._restx = divmod(self._restx + rx, ups)
        dy1, self._resty = divmod(self._resty + ry, ups)
        dx += dx1
        dy += dy1

        # scroll in the right direction
        diff = QPoint(-dx if x < 0 else dx, -dy if y < 0 else dy)
        return diff

    def finished(self):
        """As this scroller has a constant speed, it never stops."""
        return False


class KineticScroller(Scroller):
    """Scrolls the area with a decreasing speed."""
    def __init__(self):
        self._x = 0
        self._y = 0
        self._offset = None

    def scrollBy(self, diff):
        """Start a new kinetic scroll of the specified amount."""
        ### logic by Richard Cognot, May 2012, simplified by WB
        dx = diff.x()
        dy = diff.y()

        # solve speed*(speed+1)/2 = delta to ensure 1+2+3+...+speed is as close as possible under delta..
        sx = (math.sqrt(1 + 8 * abs(dx)) - 1) // 2
        sy = (math.sqrt(1 + 8 * abs(dy)) - 1) // 2

        # compute the amount of displacement still needed because we're dealing with integer values.
        # Since this function is called for exact moves (not free scrolling)
        # limit the kinetic time to 2 seconds, which means 100 ticks, 5050 pixels.
        # (TODO: adapt for other ticker speeds? WB)
        if sy > 100:
            sy = 100
        offy = abs(dy) - sy * (sy + 1) // 2

        # Although it is less likely to go beyond that limit for horizontal scrolling,
        # do it for x as well.
        if sx > 100:
            sx = 100
        offx = abs(dx) - sx * (sx + 1) // 2

        # adjust directions
        if dx < 0:
            sx = -sx
            offx = -offx
        if dy < 0:
            sy = -sy
            offy = -offy
        self._x = sx
        self._y = sy
        # the offset is accounted for in the first step
        self._offset = QPoint(offx, offy)

    def remainingDistance(self):
        """Return the remaining distance."""
        sx = abs(self._x)
        dx = sx * (sx + 1) // 2
        if self._x < 0:
            dx = -dx
        sy = abs(self._y)
        dy = sy * (sy + 1) // 2
        if self._y < 0:
            dy = -dy
        return QPoint(dx, dy)

    def step(self):
        """Return a QPoint indicating the diff to scroll in this step."""
        ret = QPoint(self._x, self._y)
        if self._offset:
            ret += self._offset
            self._offset = None
        if self._x > 0:
            self._x -= 1
        elif self._x < 0:
            self._x += 1
        if self._y > 0:
            self._y -= 1
        elif self._y < 0:
            self._y += 1
        return ret

    def finished(self):
        """Return True if scrolling is done."""
        return self._x == 0 and self._y == 0


