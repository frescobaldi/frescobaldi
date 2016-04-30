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


from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QAbstractScrollArea


from . import layout



class View(QAbstractScrollArea):
    
    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._pageLayout = layout.PageLayout()
        self.viewport().setBackgroundRole(QPalette.Dark)
    
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
    
    def _updateScrollBars(self):
        """Adjust the range of the scrollbars to the layout."""
        height = self._pageLayout.height() - self.viewport().height()
        self.verticalScrollBar().setRange(0, height)
        self.verticalScrollBar().setPageStep(self.viewport().height())
        width = self._pageLayout.width() - self.viewport().width()
        self.horizontalScrollBar().setRange(0, width)
        self.horizontalScrollBar().setPageStep(self.viewport().width())
    
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
        painter = QPainter(self.viewport())
        layout_pos = self.layoutPosition()
        for p in self.visiblePages():
            origin = p.pos() +  layout_pos
            dest_rect = p.rect().translated(layout_pos) & ev.rect()
            source_rect = dest_rect.translated(-origin)
            p.paint(painter, dest_rect, source_rect)


