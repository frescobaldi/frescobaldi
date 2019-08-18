# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
SidebarView, a special View with miniatures to use as a sidebar for a View.

Automatically displays all pages in a view in small size, and makes it easier
to browse large documents.

"""

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QPainter

from . import constants
from . import layout
from . import pagedview
from . import view



class SidebarView(pagedview.PagedViewMixin, view.View):
    """A special View with miniatures to use as a sidebar for a View.

    Automatically displays all pages in a view in small size, and makes it
    easier to browse large documents. Use connectView() to connect a View, and
    it automatically shows the pages, also when the view is changed.
    
    """
    
    MAX_ZOOM = 1.0
    pagingOnScrollEnabled = False
    wheelZoomingEnabled = False
    pageNumberDistance = 6
    firstPageNumber = 1
    scrollupdatespersec = 100
    
    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._view = None
        self.setPageLayout(SidebarLayout())
        self.setViewMode(constants.FitWidth)
        self.setLayoutFontHeight()
        self.currentPageChanged.connect(self.viewport().update)
    
    def setLayoutFontHeight(self):
        """Reads the current font height and reserves enough spacing in the layout."""
        height = self.fontMetrics().height()
        self.pageLayout().spacing = height + self.pageNumberDistance + self.pageLayout().margin
    
    def connectView(self, view):
        """Connects to a view, connecting some signals. """
        if self._view is view:
            return
        if self._view:
            self.disconnectView()
        self._view = view
        if view:
            self.currentPageChanged.connect(view.setCurrentPageNumber)
            view.currentPageChanged.connect(self.slotCurrentPageChanged)
            view.pageLayoutUpdated.connect(self.slotLayoutUpdated)
            self.slotLayoutUpdated()

    def disconnectView(self):
        """Disconnects the current view."""
        if self._view is not None:
            self.currentPageChanged.disconnect(view.setCurrentPageNumber)
            self._view.currentPageChanged.disconnect(self.slotCurrentPageChanged)
            self._view.pageLayoutUpdated.disconnect(self.slotLayoutUpdated)
    
    def slotLayoutUpdated(self):
        """Called when the layout of the connected view is updated."""
        self.pageLayout()[:] = (p.copy() for p in self._view.pageLayout())
        self.updatePageLayout()

    def slotCurrentPageChanged(self, num):
        """Called when the page number in the connected view changes.
        
        Does not scroll but updates the current page mark in our View.
        
        """
        self._currentPage = num
        self.viewport().update()

    def paintEvent(self, ev):
        """Reimplemented to print page numbers and a selection box."""
        layout_pos = self.layoutPosition()
        painter = QPainter(self.viewport())

        # pages to paint
        layout = self.pageLayout()
        ev_rect = ev.rect().translated(-layout_pos)
        pages_to_paint = set(layout.pagesAt(ev_rect))
        
        for p in pages_to_paint:
            rect = (p.geometry() & ev_rect).translated(-p.pos())
            painter.save()
            painter.translate(p.pos() + layout_pos)
            
            ## draw selection background on current page
            if p is self.currentPage():
                bg = rect.adjusted(-layout.margin, -layout.margin, layout.margin, layout.spacing-layout.margin)
                painter.fillRect(bg, self.palette().highlight())
                painter.setPen(self.palette().highlightedText().color())
            else:
                painter.setPen(self.palette().text().color())
            # draw text
            textr = QRect(rect.x(), rect.bottom(), rect.width(), layout.spacing)
            painter.drawText(textr, Qt.AlignCenter, str(layout.index(p) + self.firstPageNumber))
            painter.restore()
        super().paintEvent(ev)

    def wheelEvent(self, ev):
        """Reimplemented to page instead of scroll."""
        if ev.angleDelta().y() > 0:
            self.gotoPreviousPage()
        elif ev.angleDelta().y() < 0:
            self.gotoNextPage()

    def keyPressEvent(self, ev):
        """Reimplemented to page instead of scroll."""
        if ev.key() in (Qt.Key_PageDown, Qt.Key_Down):
            self.gotoNextPage()
        elif ev.key() in (Qt.Key_PageUp, Qt.Key_Up):
            self.gotoPreviousPage()
        elif ev.key() == Qt.Key_End:
            self.setCurrentPageNumber(self.pageCount())
        elif ev.key() == Qt.Key_Home:
            self.setCurrentPageNumber(1)
        else:
            super().keyPressEvent(ev)


class SidebarLayout(layout.PageLayout):
    """A layout that reserves space to print page numbers."""
    margin = 4
    spacing = 20
    def computeGeometry(self):
        return super().computeGeometry().adjusted(0, 0, 0, self.spacing-self.margin)
    
    def zoomFitHeight(self, height):
        """Reimplemented to take the extra spacing into account."""
        return super().zoomFitHeight(height - self.spacing + self.margin)


