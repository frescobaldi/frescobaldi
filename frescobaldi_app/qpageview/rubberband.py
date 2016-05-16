# This file is part of the qpageview package.
#
# Copyright (c) 2010 - 2016 by Wilbert Berendsen
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
Rubberband selection in a View.
"""


from PyQt5.QtCore import QEvent, QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QCursor, QPainter, QPalette, QPen, QRegion
from PyQt5.QtWidgets import QWidget


# dragging/moving selection:
_OUTSIDE = 0
_LEFT    = 1
_TOP     = 2
_RIGHT   = 4
_BOTTOM  = 8
_INSIDE  = 15


class Rubberband(QWidget):
    def __init__(self):
        super().__init__()
        self._dragging = False
        self._dragedge = 0
        self._dragpos = None
        self.setMouseTracking(True)

    def paintEvent(self, ev):
        ### Paint code contributed by Richard Cognot Jun 2012
        color = self.palette().color(QPalette.Highlight)
        painter = QPainter(self)

        # Filled rectangle.
        painter.setClipRect(self.rect())
        color.setAlpha(50)
        painter.fillRect(self.rect().adjusted(2,2,-2,-2), color)

        # Thin rectangle outside.
        color.setAlpha(150)
        painter.setPen(color)
        painter.drawRect(self.rect().adjusted(0,0,-1,-1))

        # Pseudo-handles at the corners and sides
        color.setAlpha(100)
        pen = QPen(color)
        pen.setWidth(8)
        painter.setPen(pen)
        painter.setBackgroundMode(Qt.OpaqueMode)
        # Clip at 4 corners
        region = QRegion(QRect(0,0,20,20))
        region += QRect(self.rect().width()-20, 0, 20, 20)
        region += QRect(self.rect().width()-20, self.rect().height()-20, 20, 20)
        region += QRect(0, self.rect().height()-20, 20, 20)
        # Clip middles
        region += QRect(0, self.rect().height() // 2 - 10, self.rect().width(), 20)
        region += QRect(self.rect().width() // 2 - 10, 0, 20, self.rect().height())
        
        # Draw thicker rectangles, clipped at corners and sides.
        painter.setClipRegion(region)
        painter.drawRect(self.rect())

    def edge(self, point):
        """Return the edge where the point touches our geometry."""
        rect = self.geometry()
        if point not in rect:
            return _OUTSIDE
        edge = 0
        if point.x() <= rect.left() + 4:
            edge |= _LEFT
        elif point.x() >= rect.right() - 4:
            edge |= _RIGHT
        if point.y() <= rect.top() + 4:
            edge |= _TOP
        elif point.y() >= rect.bottom() - 4:
            edge |= _BOTTOM
        return edge or _INSIDE

    def startDrag(self, pos):
        """Start dragging the rubberband."""
        self._dragging = True
        self._dragpos = pos
        self._dragedge = self.edge(pos)
        self._draggeom = self.geometry()
    
    def drag(self, pos):
        """Continue dragging the rubberband, scrolling the View if necessary."""
        diff = pos - self._dragpos
        self._dragpos = pos
        edge = self._dragedge
        self._draggeom.adjust(
            diff.x() if edge & _LEFT   else 0,
            diff.y() if edge & _TOP    else 0,
            diff.x() if edge & _RIGHT  else 0,
            diff.y() if edge & _BOTTOM else 0)
        geom = self._draggeom.normalized()
        if geom.isValid():
            self.setGeometry(geom)
        if self.cursor().shape() in (Qt.SizeBDiagCursor, Qt.SizeFDiagCursor):
            # we're dragging a corner, use correct diagonal cursor
            bdiag = (edge in (3, 12)) ^ (self._draggeom.width() * self._draggeom.height() >= 0)
            self.setCursor(Qt.SizeBDiagCursor if bdiag else Qt.SizeFDiagCursor)
    
    def stopDrag(self):
        """Stop dragging the rubberband"""
        self._dragging = False
    
    def mousePressEvent(self, ev):
        pos = self.mapToParent(ev.pos())
        if not self._dragging and ev.button() == Qt.LeftButton:
            self.startDrag(pos)
    
    def mouseMoveEvent(self, ev):
        pos = self.mapToParent(ev.pos())
        if self._dragging:
            self.drag(pos)
        else:
            edge = self.edge(pos)
            cursor = None
            if edge in (_TOP, _BOTTOM):
                cursor = Qt.SizeVerCursor
            elif edge in (_LEFT, _RIGHT):
                cursor = Qt.SizeHorCursor
            elif edge in (_LEFT | _TOP, _RIGHT | _BOTTOM):
                cursor = Qt.SizeFDiagCursor
            elif edge in (_TOP | _RIGHT, _BOTTOM | _LEFT):
                cursor = Qt.SizeBDiagCursor
            elif edge is _INSIDE:
                cursor = Qt.SizeAllCursor
            if cursor and cursor != self.cursor():
                self.setCursor(cursor)
            else:
                self.unsetCursor()
    
    def mouseReleaseEvent(self, ev):
        if self._dragging and ev.button() == Qt.LeftButton:
            self.stopDrag()


