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
The View, deriving from QAbstractScrollArea.
"""


from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QAbstractScrollArea


from . import layout



class View(QAbstractScrollArea):
    
    MIN_ZOOM = 0.05
    MAX_ZOOM = 8.0
    
    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._pageLayout = layout.PageLayout()
        self.viewport().setBackgroundRole(QPalette.Dark)
        self.verticalScrollBar().setSingleStep(20)
        self.horizontalScrollBar().setSingleStep(20)
        self.setMouseTracking(True)
    
    def setPageLayout(self, layout):
        """Set our current PageLayout instance."""
        self._pageLayout = layout
    
    def pageLayout(self):
        """Return our current PageLayout instance."""
        return self._pageLayout
    
    def updatePageLayout(self):
        """Update layout and adjust scrollbars."""
        self._pageLayout.update()
        self._updateScrollBars()
        self.viewport().update()
    
    def setZoomFactor(self, factor, pos=None):
        """Set the zoom factor (1.0 by default).
        
        If pos is given, that position (in viewport coordinates) is kept in the
        center if possible. If None, zooming centers around the viewport center.
        
        """
        if self._pageLayout.empty():
            return
        
        factor = max(self.MIN_ZOOM, min(self.MAX_ZOOM, factor))
        if factor == self._pageLayout.zoomFactor():
            return
        
        if pos is None:
            pos = self.viewport().rect().center()
        
        # find the spot on the page
        layout = self._pageLayout
        layout_pos = self.layoutPosition()
        pos_on_layout = pos - layout_pos
        page = layout.pageAt(pos_on_layout)
        if page:
            pos_on_page = pos_on_layout - page.pos()
            x = pos_on_page.x() / page.width()
            y = pos_on_page.y() / page.height()
        else:
            x = pos_on_layout.x() / layout.width()
            y = pos_on_layout.y() / layout.height()
        layout.setZoomFactor(factor)
        self.updatePageLayout()
        if page:
            new_pos_on_page = QPoint(round(x * page.width()), round(y * page.height()))
            new_pos_on_layout = page.pos() + new_pos_on_page
        else:
            new_pos_on_layout = QPoint(round(x * layout.width()), round(y * layout.height()))
        diff = new_pos_on_layout - pos
        self.verticalScrollBar().setValue(diff.y())
        self.horizontalScrollBar().setValue(diff.x())
    
    def zoomFactor(self):
        """Return the page layout's zoom factor."""
        return self._pageLayout.zoomFactor()
    
    def _updateScrollBars(self):
        """Adjust the range of the scrollbars to the layout."""
        height = self._pageLayout.height() - self.viewport().height()
        self.verticalScrollBar().setRange(0, height)
        self.verticalScrollBar().setPageStep(self.viewport().height() * .9)
        width = self._pageLayout.width() - self.viewport().width()
        self.horizontalScrollBar().setRange(0, width)
        self.horizontalScrollBar().setPageStep(self.viewport().width() * .9)
    
    def layoutPosition(self):
        """Return the position of the PageLayout relative to the viewport.
        
        This is the top-left position of the layout, relative to the
        top-left position of the viewport.
        
        If the layout is smaller than the viewport it is centered.
        
        """
        lw = self._pageLayout.width()
        vw = self.viewport().width()
        left = -self.horizontalScrollBar().value() if lw > vw else (vw - lw) // 2
        lh = self._pageLayout.height()
        vh = self.viewport().height()
        top = -self.verticalScrollBar().value() if lh > vh else (vh - lh) // 2
        return QPoint(left, top)

    def visibleRect(self):
        """Return the QRect of the page layout that is currently visible in the viewport."""
        return self.viewport().rect().translated(-self.layoutPosition())
    
    def visiblePages(self):
        """Yield the Page instances that are currently visible."""
        return self._pageLayout.pagesAt(self.visibleRect())
    
    def resizeEvent(self, ev):
        """Reimplemented to update the scrollbars."""
        self._updateScrollBars()
    
    def paintEvent(self, ev):
        layout_pos = self.layoutPosition()
        painter = QPainter(self.viewport())
        # paint the pages
        for p in self._pageLayout.pagesAt(ev.rect().translated(-layout_pos)):
            origin = p.pos() + layout_pos
            dest_rect = p.rect().translated(layout_pos) & ev.rect()
            source_rect = dest_rect.translated(-origin)
            p.paint(painter, dest_rect, source_rect)
        # TODO paint highlighting
        # TODO paint rubberband
        # TODO paint magnifier

    def wheelEvent(self, ev):
        # TEMP
        if ev.modifiers() & Qt.CTRL:
            factor = 1.1 ** (ev.angleDelta().y() / 120)
            if ev.angleDelta().y():
                self.setZoomFactor(self.zoomFactor() * factor, ev.pos())
        else:
            super().wheelEvent(ev)


