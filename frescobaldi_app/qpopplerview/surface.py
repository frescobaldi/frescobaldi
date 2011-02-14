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


from PyQt4.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt4.QtGui import QCursor, QHelpEvent, QPainter, QPalette, QRubberBand, QToolTip, QWidget

import popplerqt4

from . import layout


# most used keyboard modifiers
_SCAM = (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META)

# dragging/moving selection:
_OUTSIDE = 0
_LEFT    = 1
_TOP     = 2
_RIGHT   = 4
_BOTTOM  = 8
_INSIDE  = 15


class Surface(QWidget):
    
    selectionChanged = pyqtSignal(bool)
    
    def __init__(self, view):
        super(Surface, self).__init__(view)
        self.setBackgroundRole(QPalette.Dark)
        self._view = weakref.ref(view)
        self._currentLinkId = None
        self._dragging = False
        self._selecting = False
        self._draggingSelection = False
        self._selectionRect = QRect()
        self._rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self._pageLayout = None
        self.setPageLayout(layout.Layout())
        self.setLinksEnabled(True)
        self.setSelectionEnabled(True)
        
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
    
    def setSelectionEnabled(self, enabled):
        """Enables or disables selecting rectangular regions."""
        self._selectionEnabled = enabled
        if not enabled:
            self._rubberBand.hide()
            self._selecting = False
    
    def selectionEnabled(self):
        """Returns True if selecting rectangular regions is enabled."""
        return self._selectionEnabled
        
    def setLinksEnabled(self, enabled):
        """Enables or disables the handling of Poppler.Links in the pages."""
        self._linksEnabled = enabled
        self.setMouseTracking(enabled)
    
    def linksEnabled(self):
        """Returns True if the handling of Poppler.Links in the pages is enabled."""
        return self._linksEnabled
    
    def hasSelection(self):
        """Returns True if there is a selection."""
        return bool(self.selection())
        
    def setSelection(self, rect):
        """Sets the selection rectangle."""
        self._selectionRect = rect
        self._rubberBand.setGeometry(rect.normalized())
        self._rubberBand.setVisible(bool(rect.normalized()))
        
    def selection(self):
        """Returns the selection rectangle (normalized) or an invalid QRect()."""
        return self._selectionRect.normalized()
    
    def clearSelection(self):
        """Hides the selection rectangle."""
        self._selectionRect = QRect()
        self._rubberBand.hide()
        
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
        # link?
        if self._linksEnabled:
            page, link = self.pageLayout().linkAt(ev.pos())
            if link:
                self.linkClickEvent(ev, page, link)
                return
        # selecting?
        if self._selectionEnabled:
            if self.hasSelection():
                edge = selectionEdge(ev.pos(), self.selection())
                if edge == _OUTSIDE:
                    self.clearSelection()
                    self.selectionChanged.emit(False)
                elif ev.button() == Qt.RightButton:
                    return # dont move/resize selection with right button
                else:
                    self._selectionRect = self.selection() # force normalize
                    self._draggingSelection = edge
                    self._dragSelectPos = ev.pos()
                    return
            if not self._selecting:
                if ev.button() == Qt.RightButton or int(ev.modifiers()) & _SCAM:
                    self._selecting = True
                    self._selectPos = ev.pos()
                    self.setSelection(QRect(ev.pos(), QSize(0,0)))
                    return
        if ev.button() == Qt.LeftButton:
            self._dragging = True
            self._dragPos = ev.globalPos()
    
    def mouseReleaseEvent(self, ev):
        if self._dragging:
            self._dragging = False
        else:
            if self._selecting:
                self._selecting = False
                if self.selection().width() < 8 and self.selection().height() < 8:
                    self.clearSelection()
                self.selectionChanged.emit(self.hasSelection())
            elif self._draggingSelection:
                self._draggingSelection = False
                if self.selection().width() < 8 and self.selection().height() < 8:
                    self.clearSelection()
                self.selectionChanged.emit(self.hasSelection())
            self.updateCursor(ev.pos())
        
    def mouseMoveEvent(self, ev):
        if self._dragging:
            self.setCursor(Qt.SizeAllCursor)
            diff = ev.globalPos() - self._dragPos
            self._dragPos = ev.globalPos()
            h = self.view().horizontalScrollBar()
            v = self.view().verticalScrollBar()
            h.setValue(h.value() - diff.x())
            v.setValue(v.value() - diff.y())
        elif self._selecting:
            self.setSelection(QRect(self._selectPos, ev.pos()))
        elif self._draggingSelection:
            diff = ev.pos() - self._dragSelectPos
            self._dragSelectPos = ev.pos()
            sel = self._draggingSelection
            self.setSelection(self._selectionRect.adjusted(
                diff.x() if sel & _LEFT   else 0,
                diff.y() if sel & _TOP    else 0,
                diff.x() if sel & _RIGHT  else 0,
                diff.y() if sel & _BOTTOM else 0))
        else:
            self.updateCursor(ev.pos())
    
    def moveEvent(self, ev):
        if not self._dragging:
            self.updateCursor(self.mapFromGlobal(QCursor.pos()))
        
    def event(self, ev):
        if isinstance(ev, QHelpEvent):
            if self._linksEnabled:
                page, link = self.pageLayout().linkAt(ev.pos())
                if link:
                    QToolTip.showText(ev.globalPos(), link.url(), self, page.linkRect(link))
            return True
        return super(Surface, self).event(ev)

    def updateCursor(self, pos):
        cursor = None
        if self._selectionEnabled and self.hasSelection():
            edge = selectionEdge(pos, self.selection())
            if edge in (_TOP, _BOTTOM):
                cursor = Qt.SizeVerCursor
            elif edge in (_LEFT, _RIGHT):
                cursor = Qt.SizeHorCursor
            elif edge in (_LEFT | _TOP, _RIGHT | _BOTTOM):
                cursor = Qt.SizeFDiagCursor
            elif edge in (_TOP | _RIGHT, _BOTTOM | _LEFT):
                cursor = Qt.SizeBDiagCursor
        if cursor is None and self._linksEnabled:
            page, link = self.pageLayout().linkAt(pos)
            if link:
                cursor = Qt.PointingHandCursor
                lid = id(link)
            else:
                lid = None
            if lid != self._currentLinkId:
                if self._currentLinkId is not None:
                    self.linkHoverLeave()
                self._currentLinkId = lid
                if link:
                    self.linkHoverEnter(page, link)
        self.setCursor(cursor) if cursor else self.unsetCursor()
        
    def linkClickEvent(self, ev, page, link):
        """Called when a link is clicked."""
        print "linkClickEvent", link.url()
        
    def linkHoverEnter(self, page, link):
        """Called when the mouse hovers over a link."""
        print "linkHoverEnter", link.url()
        
    def linkHoverLeave(self):
        """Called when the mouse does not hover a link anymore."""
        print "linkHoverLeave"



def selectionEdge(point, rect):
    """Returns the edge where the point touches the rect."""
    if point not in rect.adjusted(-2, -2, 2, 2):
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

