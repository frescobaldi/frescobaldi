# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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

from PyQt4.QtCore import QTimeLine, pyqtSignal
from PyQt4.QtGui import QPainter, QPalette, QPen, QWidget


def blink(widget, rect, color=None):
    """Shortly blinks a rectangular region on a widget.
    
    If color is not given, the highlight color of the widget is used.
    
    """
    window = widget.window()
    rect.moveTo(widget.mapTo(window, rect.topLeft()))
    b = Blinker(window)
    p = widget.palette()
    if color:
        p.setColor(QPalette.Highlight, color)
    b.setPalette(p)
    b.blink(rect)
    b.finished.connect(b.deleteLater)


class Blinker(QWidget):
    """Can draw a blinking region above its parent widget."""
    
    finished = pyqtSignal()
    
    lineWidth = 4
    radius = 3
    
    def __init__(self, widget):
        """Initializes ourselves to draw on the widget."""
        super(Blinker, self).__init__(widget)
        self.timeLine = QTimeLine()
        self.timeLine.setDuration(1000)
        self.timeLine.setCurveShape(QTimeLine.LinearCurve)
        self.timeLine.setUpdateInterval(40)
        self.timeLine.frameChanged.connect(self._updateFrame)
        self.timeLine.finished.connect(self.done)
        
    def blink(self, rect):
        """Starts blinking the specified rectangle."""
        self._blink_rect = rect
        adj = self.lineWidth
        self.setGeometry(rect.adjusted(-adj, -adj, adj, adj))
        self.show()
        self.timeLine.setFrameRange(1040, 40)
        self.timeLine.start()
        
    def done(self):
        """(Internal) Called when the animation ends."""
        self.hide()
        self.finished.emit()
    
    def _updateFrame(self, frame):
        self.update()
    
    def animationColor(self):
        """Returns a color to animate the blinking."""
        frame = self.timeLine.currentFrame()
        if frame > 255:
            if (frame + 1) % 200 > 100:
                alpha = 0
            else:
                alpha = 255
        else:
            alpha = frame
        color = self.palette().color(QPalette.Highlight)
        if color.alpha() > alpha:
            color.setAlpha(alpha)
        return color
        
    def paintEvent(self, ev):
        color = self.animationColor()
        if color.alpha() == 0:
            return
        painter = QPainter(self)
        adj = self.lineWidth / 2
        rect = self.rect().adjusted(adj, adj, -adj, -adj)
        pen = QPen(color)
        pen.setWidth(self.lineWidth)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawRoundedRect(rect, self.radius, self.radius)


