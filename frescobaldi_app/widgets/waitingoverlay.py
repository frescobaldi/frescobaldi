# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
Animated "waiting" overlay to be attached to arbitrary widgets.

Create an Overlay object and make sure it has a QWidget as parent.
With start() and stop() a (semi-) transparent waiting animation is
centered over the parent widget.
"""

# Modified after
# https://wiki.python.org/moin/PyQt/A%20full%20widget%20waiting%20indicator

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen
)
from PyQt5.QtWidgets import (
    QWidget
)

class Overlay(QWidget):
    """
    Transparent overlay widget displaying a "waiting" animation
    centered over its parent widget.
    - interval: update interval in ms
    - transparency: transparency (0-255) of the effect background.
    """

    # TODO: Add more configuration options (background and foreground colors)
    def __init__(
        self,
        parent=None,
        interval=75,
        transparency=200
    ):
        super().__init__(parent)
        self._counter = 0
        self._timerId = None
        self.setTransparency(transparency)
        self.setInterval(interval)
        self.hide()

    def paintEvent(self, event):
        """Repaint the widget.

        First create a (semi-) transparent background for the whole
        parent widget, then paint six small circles, with one
        colored differently.
        """

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(
            event.rect(), QColor(255, 255, 255, self._transparency)
        )
        painter.setPen(QPen(Qt.NoPen))
        painter.translate(self.rect().center())

        for i in range(6):
            if (self._counter // 5) % 6 == i:
                painter.setBrush(
                    QBrush(QColor(127 + (self._counter % 5)*32, 127, 127))
                )
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(30, -10, 20, 20)
            painter.rotate(60)
        painter.end()

    def setInterval(self, value):
        """Change the timer interval (ms)."""
        self._interval = value

    def setTransparency(self, value):
        """Set the transparency of the animation background,
        input is limited to 0-255."""
        value = max(0, min(255, value))
        self._transparency = 255 - value

    def start(self):
        """Show the overlay and start the animation."""
        self._timerId = self.startTimer(self._interval)
        self.resize(self.parent().size())
        self.show()

    def stop(self):
        """Stop the animation and hide the overlay."""
        if self._timerId is not None:
            self.killTimer(self._timerId)
            self._timerId = None
        self.hide()
        self._counter = 0

    def timerEvent(self, ev):
        self._counter += 1
        self.resize(self.parent().size())
        self.update()
