# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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
Surface is the widget everything is drawn on.
"""

import weakref


from PyQt4.QtCore import QPoint, QRect, Qt
from PyQt4.QtGui import QCursor, QHelpEvent, QPainter, QPalette, QToolTip, QWidget

import popplerqt4

from . import layout


class Surface(QWidget):
    def __init__(self, view):
        super(Surface, self).__init__(view)
        self.setBackgroundRole(QPalette.Dark)
        self._view = weakref.ref(view)
        self._pageLayout = None
        self.setPageLayout(layout.Layout())
        self.setMouseTracking(True)
        self._currentLinkId = None
        self._dragging = False
        
    def pageLayout(self):
        return self._pageLayout
        
    def setPageLayout(self, layout):
        old, self._pageLayout = self._pageLayout, layout
        if old:
            old.redraw.disconnect(self.redraw)
        layout.redraw.connect(self.redraw)
    
    def view(self):
        """Returns our associated View."""
        return self._view()
        
    def redraw(self, rect):
        """Called when the Layout wants to redraw a rectangle."""
        self.update(rect)
        
    def updateLayout(self):
        """Conforms ourselves to our layout (that must already be updated.)"""
        self.resize(self._pageLayout.size())
        self.update()
        
    def paintEvent(self, ev):
        painter = QPainter(self)
        for page in self.pageLayout().pagesAt(ev.rect()):
            page.paint(painter, ev.rect())
    
    def mousePressEvent(self, ev):
        page, link = self.pageLayout().linkAt(ev.pos())
        if link:
            self.linkClickEvent(ev, page, link)
        elif ev.button() == Qt.LeftButton:
            self._dragging = True
            self._dragPos = ev.globalPos()
    
    def mouseReleaseEvent(self, ev):
        if self._dragging and ev.button() == Qt.LeftButton:
            self._dragging = False
            self.updateCursor(ev.pos())
            
    def mouseMoveEvent(self, ev):
        if self._dragging and ev.buttons() == Qt.LeftButton:
            self.setCursor(Qt.SizeAllCursor)
            diff = ev.globalPos() - self._dragPos
            self._dragPos = ev.globalPos()
            h = self.view().horizontalScrollBar()
            v = self.view().verticalScrollBar()
            h.setValue(h.value() - diff.x())
            v.setValue(v.value() - diff.y())
        else:
            self.updateCursor(ev.pos())
    
    def moveEvent(self, ev):
        if not self._dragging:
            self.updateCursor(self.mapFromGlobal(QCursor.pos()))
        
    def event(self, ev):
        if isinstance(ev, QHelpEvent):
            page, link = self.pageLayout().linkAt(ev.pos())
            if link:
                QToolTip.showText(ev.globalPos(), link.url(), self, page.linkRect(link))
            return True
        return super(Surface, self).event(ev)

    def updateCursor(self, pos):
        page, link = self.pageLayout().linkAt(pos)
        lid = id(link) if link else None
        if lid != self._currentLinkId:
            if self._currentLinkId is not None:
                self.linkHoverLeave()
            self._currentLinkId = lid
            if link:
                self.linkHoverEnter(page, link)
        self.setCursor(Qt.PointingHandCursor) if link else self.unsetCursor()
        
    def linkClickEvent(self, ev, page, link):
        """Called when a link is clicked."""
        print "linkClickEvent", link.url()
        
    def linkHoverEnter(self, page, link):
        """Called when the mouse hovers over a link."""
        print "linkHoverEnter", link.url()
        
    def linkHoverLeave(self):
        """Called when the mouse does not hover a link anymore."""
        print "linkHoverLeave"



