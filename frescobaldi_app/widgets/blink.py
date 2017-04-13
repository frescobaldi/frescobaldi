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
Shortly blinks a region on a widget.
"""

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFontMetrics, QPainter, QPalette, QPen
from PyQt5.QtWidgets import QWidget


class Blinker(QWidget):
    """Can draw a blinking region above its parent widget."""

    finished = pyqtSignal()

    lineWidth = 3
    radius = 3

    @classmethod
    def blink(cls, widget, rect=None, color=None):
        """Shortly blinks a rectangular region on a widget.

        If rect is not given, the full rect() of the widget is used.
        If color is not given, the highlight color of the widget is used.
        This method instantiates a Blinker widget and discards it after use.

        """
        window = widget.window()
        if rect is None:
            rect = widget.rect()
        rect.moveTo(widget.mapTo(window, rect.topLeft()))
        b = cls(window)
        p = widget.palette()
        if color:
            p.setColor(QPalette.Highlight, color)
        b.setPalette(p)
        b.start(rect)
        b.finished.connect(b.deleteLater)

    @classmethod
    def blink_cursor(cls, textedit, color=None):
        """Highlights the cursor in a Q(Plain)TextEdit."""
        metrics = QFontMetrics(textedit.textCursor().charFormat().font())
        width = metrics.boundingRect("m").width()
        rect = textedit.cursorRect().normalized().adjusted(0, 0, width, 0)
        cls.blink(textedit, rect.translated(textedit.viewport().pos()), color)

    def __init__(self, widget):
        """Initializes ourselves to draw on the widget."""
        super(Blinker, self).__init__(widget)
        self._color = None
        self._animation = ()
        self._timer = QTimer(singleShot=True, timeout=self._updateAnimation)

    def start(self, rect):
        """Starts blinking the specified rectangle."""
        self._blink_rect = rect
        adj = self.lineWidth
        self.setGeometry(rect.adjusted(-adj, -adj, adj, adj))
        self.show()
        self._animation = self.animateColor()
        self._updateAnimation()

    def done(self):
        """(Internal) Called when the animation ends."""
        self.hide()
        self._animation = ()
        self.finished.emit()

    def _updateAnimation(self):
        for delta, self._color in self._animation:
            self.update()
            self._timer.start(delta)
            return
        self.done()

    def animateColor(self):
        """A generator yielding tuples (msec_delta, color) to animate colors.

        When the generator exits, the animation ends.
        The color is taken from the Highlight palette value.

        """
        color = self.palette().color(QPalette.Highlight)
        for delta, alpha in self.animateAlpha():
            color.setAlpha(alpha)
            yield delta, color

    def animateAlpha(self):
        """A generator yielding (msec_delta, alpha) tuples."""
        for alpha in (255, 0, 255, 0, 255):
            yield 120, alpha
        for alpha in range(255, 0, -15):
            yield 40, alpha

    def paintEvent(self, ev):
        color = self._color
        if not color or color.alpha() == 0:
            return
        painter = QPainter(self)
        adj = self.lineWidth // 2
        rect = self.rect().adjusted(adj, adj, -adj, -adj)
        pen = QPen(color)
        pen.setWidth(self.lineWidth)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawRoundedRect(rect, self.radius, self.radius)


