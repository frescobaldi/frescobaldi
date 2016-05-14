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
The Magnifier magnifies a part of the displayed document.
"""

import weakref

from PyQt5.QtCore import QEvent, QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QPainter, QPalette, QPen, QRegion
from PyQt5.QtWidgets import QWidget


class Magnifier(QWidget):
    """A Magnifier is added to a View with surface.setMagnifier().
    
    It is shown when a mouse button is pressed together with a modifier
    (by default Ctrl, see view.py).
    
    Its size can be changed with resize() and the scale (defaulting to 3.0)
    with setScale().
    
    """
    
    # Maximum extra zoom above the View.MAX_ZOOM
    MAX_EXTRA_ZOOM = 1.25
    
    def __init__(self):
        super().__init__()
        self._dragging = False
        self._pages = weakref.WeakKeyDictionary()
        self._scale = 3.0
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.Dark)
        self.resize(250, 250)
        self.hide()
        
    def moveCenter(self, pos):
        """Called by the View, centers the widget on the given QPoint."""
        r = self.geometry()
        r.moveCenter(pos)
        self.setGeometry(r)
    
    def setScale(self, scale):
        """Sets the scale, relative to the dislayed size in the View."""
        self._scale = scale
        self.update()
    
    def scale(self):
        """Returns the scale, defaulting to 3.0 (=300%)."""
        return self._scale
    
    def resizeEvent(self, ev):
        """Called on resize, sets our circular mask."""
        self.setMask(QRegion(self.rect(), QRegion.Ellipse))
        
    def eventFilter(self, obj, ev):
        """Reimplemented to update on View scroll."""
        if ev.type() == QEvent.UpdateRequest:
            self.update()
        return False
    
    def mousePressEvent(self, ev):
        """Start dragging the magnifier."""
        if ev.button() == Qt.LeftButton:
            self._dragging = True
            self._dragpos = ev.pos()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, ev):
        """Move the magnifier if we were dragging it."""
        if self._dragging:
            self.move(self.mapToParent(ev.pos()) - self._dragpos)
    
    def mouseReleaseEvent(self, ev):
        """The button is released, stop moving ourselves."""
        if ev.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self.unsetCursor()
    
    def paintEvent(self, ev):
        """Called when paint is needed, finds out which page to magnify."""
        view = self.parent().parent()
        layout = view.pageLayout()
        
        scale = min(self._scale, view.MAX_ZOOM * self.MAX_EXTRA_ZOOM / layout.zoomFactor)
        
        # the position of our center on the layout
        c = self.rect().center() + self.pos() - view.layoutPosition()
        
        # make a region scaling back to the view scale
        rect = QRect(0, 0, self.width() / scale, self.height() / scale)
        rect.moveCenter(c)
        region = QRegion(rect, QRegion.Ellipse) # touches the Pages we need to draw
        
        # our rect on the enlarged pages
        our_rect = self.rect()
        our_rect.moveCenter(QPoint(c.x() * scale, c.y() * scale))
        
        # the virtual position of the whole scaled-up layout
        ev_rect = ev.rect().translated(our_rect.topLeft())
        
        painter = QPainter(self)
        for p in layout.pagesAt(region):
            # reuse the copy of the page if still existing
            try:
                page = self._pages[p]
            except KeyError:
                page = self._pages[p] = p.copy()
            page.x = p.x * scale
            page.y = p.y * scale
            page.width = p.width * scale
            page.height = p.height * scale
            # now paint it
            rect = (page.rect() & ev_rect).translated(-page.pos())
            painter.save()
            painter.translate(page.pos() - our_rect.topLeft())
            page.paint(painter, rect, self.repaintPage)
            painter.restore()
        # draw a nice looking glass border
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(192, 192, 192, 128), 6))
        painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))

    def repaintPage(self, page):
        """Called when a Page was rendered in the background."""
        ## TODO: smarter determination which part to update
        self.update()


