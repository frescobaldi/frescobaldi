# This file is part of the qpopplerview package.
#
# Copyright (c) 2010 - 2014 by Wilbert Berendsen
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
KineticScrollArea widget to provide kinetic scrolling moves.
"""


from PyQt5.QtCore import QPoint, QBasicTimer, QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QMouseEvent
from PyQt5.QtWidgets import QScrollArea, QApplication

from math import sqrt
import copy



# most used keyboard modifiers
_SCAM = (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META)

def deaccelerate(speed, a=1, maxVal=64):
    x = qBound(-maxVal, speed.x(), maxVal)
    y = qBound(-maxVal, speed.y(), maxVal)
    if x > 0:
        x = max(0, x - a)
    elif x < 0:
        x = min(0, x + a)
    if y > 0:
        y = max(0, y - a)
    elif y < 0:
        y = min(0, y + a)
    return QPoint(x, y)


def qBound(minVal, current, maxVal):
    return max(min(current, maxVal), minVal)

# Centralize data for kinetic scrolling
class KineticData:

    Steady = 0
    Pressed = 1
    ManualScroll = 2
    AutoScroll = 3
    Stop = 4

    def __init__(self):
        self._state = KineticData.Steady
        self._pressPos = QPoint(0, 0)
        self._offset = QPoint(0, 0)
        self._dragPos = QPoint(0, 0)
        self._speed = QPoint(0, 0)
        self._maxSpeed = 64
        self._ignored = []
        self._ticker = QBasicTimer()

    def ignoreEvent(self, ev):
        found = False
        ignored = []
        for event in self._ignored:
            if event == ev:
                found = True
            else:
                ignored.append(event)
        if found :
            self._ignored = ignored

        return found

import array

class KineticScrollArea(QScrollArea):

    # signal emitted when kinetic scrolling starts/stops, to make it possible
    # to shut down some event listeners until we're done.
    kineticScrollingActive = pyqtSignal(bool)
    cursorNeedUpdate = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        super(KineticScrollArea, self).__init__(parent)

        # kinetic scrolling
        self._kineticScrollingEnabled = False
        self._scrollFuncIndex = 0

        # Functions pointers, index 0 -> kinetic, index 1 -> classic.
        self._scrollBy = [
            self.kineticScrollBy,
            self.fastScrollBy
        ]
        self._center = [
            self.kineticCenter,
            self.fastCenter
        ]
        self._ensureVisible = [
            self.kineticEnsureVisible,
            super(KineticScrollArea, self).ensureVisible
        ]

        self._scrollbarsVisible = True
        self._kineticData=KineticData()

        self._dragging = False


    def setScrollbarsVisible(self, enabled):
        """Sets the scrollbars visibility status."""
        self._scrollbarsVisible = enabled

        if enabled:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def scrollbarsVisible(self):
        """Returns the current scrollbars visibility status"""

        return self._scrollbarsVisible

    def setKineticScrolling(self, enabled):
        """Sets whether kinetic scrolling is enabled or not."""

        self._kineticScrollingEnabled = enabled
        if enabled:
            self._scrollFuncIndex = 0
        else:
            self._scrollFuncIndex = 1

    def kineticScrollingEnabled(self):
        """Returns whether kinetic scrolling is enabled."""

        return self._kineticScrollingEnabled

    def kineticIsIdle(self):
        return self._kineticData._state == KineticData.Steady

    def scrollOffset(self):
        """Get the current scroll position."""

        x = self.horizontalScrollBar().value()
        y = self.verticalScrollBar().value()
        return QPoint(x, y)


    def setScrollOffset(self, p):
        """Set the current scroll position. Returns true if at last one of (x,y) was really modified."""
        start_p = self.scrollOffset()

        self.horizontalScrollBar().setValue(p.x())
        self.verticalScrollBar().setValue(p.y())
        # return true if at least one coordinate specified was respected and requested move was not 0.
        end_p = self.scrollOffset()
        return (start_p.x() != p.x() and end_p.x() == p.x()) or (start_p.y() != p.y() and end_p.y() == p.y())

    def fastScrollBy(self, diff):
        """Immediately Scrolls by the distance given in the QPoint diff."""
        v = self.verticalScrollBar()
        h = self.horizontalScrollBar()
        v.setValue(v.value() + diff.y())
        h.setValue(h.value() + diff.x())

    def kineticScrollBy(self, diff):
        """Kinetically Scrolls by the distance given in the QPoint diff."""
        v = self.verticalScrollBar()
        h = self.horizontalScrollBar()
        self.kineticMove(h.value(), v.value(), h.value()+diff.x(), v.value()+diff.y())

    def scrollBy(self, diff):
        """Scrolls by the distance given in the QPoint diff.
        Scrolling will either be immediate or kinetic.
        """
        self._scrollBy[self._scrollFuncIndex](diff)

    def fastCenter(self, point):
        """Immediately center the view on the given QPoint"""

        diff = point - self.viewport().rect().center() + self.widget().pos()
        self.fastScrollBy(diff)

    def kineticCenter(self, point):
        """Kinetically center the view on the given QPoint"""

        size = self.widget().viewportRect().size()
        self.kineticEnsureVisible(point.x(), point.y(),
                                  size.width() // 2, size.height() // 2)

    def center(self, point, overrideKinetic=False):
        """Centers the given QPoint of the widget.
        Centering will either be immediate or kinetic."""
        self._center[self._scrollFuncIndex](point)

    def kineticMove(self, oldx, oldy, newx, newy ):
        """Start a kinetic move from (oldx, oldy) to (newx, newy)"""
        if newx == oldx and newy == oldy:
            return

        speed = QPoint(0,0)
        # solve speed*(speed+1)/2 = delta to ensure 1+2+3+...+speed is as close as possible under delta..
        speed.setX((sqrt(1+8*abs(newx-oldx))-1)/2)
        speed.setY((sqrt(1+8*abs(newy-oldy))-1)/2)

        # compute the amount of displacement still needed because we're dealing with integer values.
        diff = QPoint(0,0)
        diff.setX((speed.x() * (speed.x() + 1) // 2) - abs(newx - oldx))
        diff.setY((speed.y() * (speed.y() + 1) // 2) - abs(newy - oldy))

        # Since this function is called for exact moves (not free scrolling)
        # limit the kinetic time to 2 seconds, which means 100 ticks, 5050 pixels.
        if speed.y() > 100:
            speed.setY(100)
            diff.setY(-abs(newy-oldy) + 5050)

        # Although it is less likely to go beyond that limit for horizontal scrolling,
        # do it for x as well.
        if speed.x() > 100:
            speed.setX(100)
            diff.setX(-abs(newx-oldx) + 5050)

        # move left or right, up or down
        if newx > oldx :
            speed.setX(-speed.x())
            diff.setX(-diff.x())
        if newy > oldy :
            speed.setY(-speed.y())
            diff.setY(-diff.y())

        # move immediately by the step that cannot be handled by kinetic scrolling.
        # By construction that step is smaller that the initial speed value.
        self.fastScrollBy(diff)

        self.kineticStart(speed)

    def kineticAddDelta(self, delta):
        """Add a kinetic delta to an already started kinetic move.

        Delta is a QPoint, with respectively the changes in x and y position.

        """
        def compute_speed(s, d):
            if d:
                # Get the remaining scroll amount.
                currentSpeed = abs( s )
                leftToScroll = (currentSpeed + 1) * currentSpeed // 2
                if s < 0:
                    leftToScroll *= -1
                leftToScroll += d

                s = (sqrt(1+8*abs(leftToScroll))-1)/2
                if leftToScroll < 0:
                    s = -s
            return s

        speed_x = compute_speed(self._kineticData._speed.x(), delta.x())
        speed_y = compute_speed(self._kineticData._speed.y(), delta.y())
        speed = QPoint(speed_x, speed_y)
        self.kineticStart(speed)

    def kineticStart(self, speed):
        """Start kinetic scrolling with a given speed. Speed will be decremented periodically
        until scrolling halts."""
        # Setup the kinetic displacement speed, removing the speed limit imposed on
        # interactive scrolling.
        self._kineticData._speed = speed
        # speed limit is one above speed, to make sure there will be none.
        self._kineticData._maxSpeed = max(abs(speed.x()), abs(speed.y())) + 1

        # Set kinetic state to AutoScroll, the reference position to the current view center,
        # and fire the timer.
        self._kineticData._state = KineticData.AutoScroll
        self._kineticData._dragPos = self.pos()
        if not self._kineticData._ticker.isActive():
            self._kineticData._ticker.start(20, self)
            self.kineticScrollingActive.emit(True)

    def kineticTicksLeft(self):
        """Return the number of ticks left on the kinetic counter."""
        if( self._kineticData._state == KineticData.AutoScroll
            or self._kineticData._state == KineticData.ManualScroll ):
            return max( abs(self._kineticData._speed.x()), abs(self._kineticData._speed.y()) )

        return 0

    def kineticEnsureVisible(self, x, y, xm, ym):
        """Ensure a given point is visible, with a margin, by starting the appropriate kinetic scrolling."""
        # Replicate the logic in ScrollArea::ensureVisible to compute the
        # scrollbar displacements, per Qt sources.
        oldx = self.horizontalScrollBar().value()
        oldy = self.verticalScrollBar().value()

        newx = oldx
        if x-xm < oldx :
            newx = max(0, x - xm)
        elif x > oldx + self.viewport().width() - xm:
            newx = min(x - self.viewport().width() + xm, self.verticalScrollBar().maximum())

        newy = oldy
        if y-ym < oldy :
            newy = max(0, y - ym)
        elif y > oldy + self.viewport().height() - ym:
            newy = min(y - self.viewport().height() + ym, self.verticalScrollBar().maximum())

        self.kineticMove(oldx, oldy, newx, newy)

    def ensureVisible(self, x, y, xm=50, ym=50):
        """
        Reimplement ensureVisible to call the kinetic scroller timer if kinetic scrolling is enabled.
        """

        self._ensureVisible[self._scrollFuncIndex](x, y, xm, ym)

    def wheelEvent(self, ev):
        """Kinetic wheel movements, if enabled."""
        if self._kineticScrollingEnabled:
            self.kineticAddDelta(ev.angleDelta())
        else:
            super(KineticScrollArea, self).wheelEvent(ev)

    def keyPressEvent(self, ev):
        """Kinetic cursor movements, if enabled."""
        if self._kineticScrollingEnabled:
            if ev.key() == Qt.Key_PageDown:
                self.kineticAddDelta(QPoint(0, -self.verticalScrollBar().pageStep()))
                return
            elif ev.key() == Qt.Key_PageUp:
                self.kineticAddDelta(QPoint(0, self.verticalScrollBar().pageStep()))
                return
            elif ev.key() == Qt.Key_Down:
                self.kineticAddDelta(QPoint(0, -self.verticalScrollBar().singleStep()))
                return
            elif ev.key() == Qt.Key_Up:
                self.kineticAddDelta(QPoint(0, self.verticalScrollBar().singleStep()))
                return
            elif ev.key() == Qt.Key_Home:
                self.kineticMove(0, self.verticalScrollBar().value(), 0, 0)
                return
            elif ev.key() == Qt.Key_End:
                self.kineticMove(0, self.verticalScrollBar().value(), 0, self.verticalScrollBar().maximum())
                return
        else:
            # Home/End are not handled by default.
            if ev.key() == Qt.Key_Home:
                self.setScrollOffset(QPoint(0,0))
                return
            elif ev.key() == Qt.Key_End:
                self.setScrollOffset(QPoint(self.horizontalScrollBar().maximum(), self.verticalScrollBar().maximum()))
                return

        super(KineticScrollArea, self).keyPressEvent(ev)

    def mousePressEvent(self, ev):
        """Handle mouse press for dragging start/stop."""
        if ev.button() == Qt.LeftButton:
            self._dragPos = ev.globalPos()

            if self._kineticScrollingEnabled:
                # kinetic scrolling
                if self._kineticData.ignoreEvent(ev):
                    return

                if self._kineticData._state == KineticData.Steady or self._kineticData._state == KineticData.Stop:
                    self._dragging = True
                    self._kineticData._state = KineticData.Pressed
                    self._kineticData._pressPos = copy.copy(ev.pos())
                    self._kineticData._offset = self.scrollOffset()
                    self._kineticData._maxSpeed = 64 #limit speed.

                elif self._kineticData._state == KineticData.AutoScroll:
                    self._dragging = True
                    self._kineticData._state = KineticData.Stop
                    self._kineticData._speed = QPoint(0,0)
            else:
                self._dragging = True

        super(KineticScrollArea, self).mousePressEvent(ev)


    def mouseReleaseEvent(self, ev):
        """Handle mouse release events for kinetic dragging end/auto mode."""
        if self._dragging:
            self._dragging = False
            self.unsetCursor()
            if self._kineticScrollingEnabled:
                # kinetic scrolling
                if self._kineticData.ignoreEvent(ev):
                    return

                if self._kineticData._state == KineticData.Pressed:
                    self._kineticData._state = KineticData.Steady
                    event1 = QMouseEvent(QEvent.MouseButtonPress,
                                         self._kineticData._pressPos, Qt.LeftButton,
                                         Qt.LeftButton, Qt.NoModifier)
                    event2 = QMouseEvent(ev)
                    self._kineticData._ignored.append(event1)
                    self._kineticData._ignored.append(event2)
                    QApplication.postEvent(self, event1)
                    QApplication.postEvent(self, event2)

                elif self._kineticData._state == KineticData.ManualScroll:
                    self._kineticData._state = KineticData.AutoScroll

                elif self._kineticData._state == KineticData.AutoScroll:
                    self._kineticData._state = KineticData.Stop
                    self._kineticData._speed = QPoint(0, 0)

                elif self._kineticData._state == KineticData.Stop:
                    self._kineticData._state = KineticData.Steady

        if self._kineticData._state == KineticData.Steady:
            self.cursorNeedUpdate.emit(ev.globalPos())

        super(KineticScrollArea, self).mouseReleaseEvent(ev)

    def mouseMoveEvent(self, ev):
        """Handle mouse move events for kinetic dragging timer firing.
        Notifies cursor needs update if no kinetic move is active.
        """
        if self._dragging:
            self.setCursor(Qt.SizeAllCursor)

            if self._kineticScrollingEnabled:
                # kinetic scrolling
                if self._kineticData.ignoreEvent(ev):
                    return

                if self._kineticData._state == KineticData.Pressed:
                    self._kineticData._state = KineticData.ManualScroll
                    self._kineticData._dragPos = QCursor.pos()
                    if not self._kineticData._ticker.isActive():
                        self._kineticData._ticker.start(20, self)
                        self.kineticScrollingActive.emit(True)

                elif self._kineticData._state == KineticData.ManualScroll:
                    diff = self._dragPos - ev.globalPos()
                    self._dragPos = ev.globalPos()
                    self.fastScrollBy(diff)

                elif self._kineticData._state == KineticData.Stop:
                    self._kineticData._state = KineticData.ManualScroll
                    self._kineticData._dragPos = QCursor.pos()
                    if not self._kineticData._ticker.isActive():
                        self._kineticData._ticker.start(20, self)
                        self.kineticScrollingActive.emit(True)

            else:
                diff = self._dragPos - ev.globalPos()
                self._dragPos = ev.globalPos()
                self.fastScrollBy(diff)

        super(KineticScrollArea, self).mouseMoveEvent(ev)

        if self.kineticIsIdle():
            self.cursorNeedUpdate.emit(ev.globalPos())

    def moveEvent(self, ev):
        """Move event handler. Passes the event to the base class and notify the cursor needs update."""
        super(KineticScrollArea, self).moveEvent(ev)

        if self.kineticIsIdle():
            self.cursorNeedUpdate.emit(QCursor.pos())

    def timerEvent(self, event):
        """Handle events sent by the kinetic timer to decrease progressively
           the scrolling speed, eventually halting it.
        """
        count = 0
        if self._kineticData._state == KineticData.ManualScroll:
            count += 1
            cursorPos = QCursor.pos()
            self._kineticData._speed = cursorPos - self._kineticData._dragPos
            self._kineticData._dragPos = cursorPos
        elif self._kineticData._state == KineticData.AutoScroll:
            count += 1
            p = self.scrollOffset()

            if self._kineticData._speed == QPoint(0, 0) or not self.setScrollOffset(p - self._kineticData._speed):
                self._kineticData._state = KineticData.Steady
                # reset speed to 0, as wheel scrolling accumulates speed instead of setting it to a fixed value.
                self._kineticData._speed = QPoint(0,0)
                # reset count to 0 to stop iterating.
                count = 0

            self._kineticData._speed = deaccelerate(self._kineticData._speed, 1, self._kineticData._maxSpeed)

        if count == 0:
            self._kineticData._ticker.stop()
            self.kineticScrollingActive.emit(False)

        super(KineticScrollArea, self).timerEvent(event)
