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

import math

from PyQt5.QtCore import (
    Qt,
    QTimer
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPalette,
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
        super(Overlay, self).__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)
        self.setTransparency(transparency)
        self._counter = 0
        self._timer = QTimer()
        self._timer.setInterval(interval)
        self.setInterval(interval)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self.next)
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
            event.rect(), QBrush(QColor(255, 255, 255, self._bgcolor))
        )
        painter.setPen(QPen(Qt.NoPen))

        for i in range(6):
            if (self._counter // 5) % 6 == i:
                painter.setBrush(
                    QBrush(QColor(127 + (self._counter % 5)*32, 127, 127))
                )
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(
                self.width()/2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                self.height()/2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                20, 20)

        painter.end()

    def setInterval(self, value):
        """Change the timer interval (ms)."""
        self._timer.setInterval(value)

    def setTransparency(self, value):
        """Set the transparency of the animation background,
        input is limited to 0-255."""
        value = max(0, min(255, value))
        self._bgcolor = 255 - value

    def start(self):
        """Show the overlay and start the animation."""
        self._timer.start()
        self.resize(self.parent().size())
        self.show()

    def stop(self):
        """Stop the animation and hide the overlay."""
        self._timer.stop()
        self.hide()
        self._counter = 0

    def next(self):
        self._counter += 1
        self.update()
