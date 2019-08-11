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
Mixin class to add paging capabilities to View.
"""

from PyQt5.QtCore import pyqtSignal


class PagedViewMixin:
    """Mixin class to add paging capabilities to View.

    These instance variables influence the behaviour:

    `kineticPagingEnabled`  (True by default) Whether to scroll smoothly when
                            setCurrentPage() is called.

    `pagingOnScrollEnabled` (True by default) Whether the current page number
                            is updated when the user scrolls the view.

    """
    
    pageCountChanged = pyqtSignal(int)
    currentPageChanged = pyqtSignal(int)
    
    kineticPagingEnabled = True  # whether to smoothly scroll on setCurrentPage
    pagingOnScrollEnabled = True # keep track of current page while scrolling
    
    def __init__(self, parent=None, **kwds):
        self._pageCount = 0
        self._currentPage = 0
        self._scrollingToPage = False   # keep track of scrolling/page numbers
        super().__init__(parent, **kwds)

    def mousePressEvent(self, ev):
        """Implemented to set the clicked page as current."""
        page = self._pageLayout.pageAt(ev.pos() - self.layoutPosition())
        if page:
            self.setCurrentPage(self._pageLayout.index(page) + 1)
        super().mousePressEvent(ev)

    def pageCount(self):
        """Return the number of pages currently in view."""
        return self._pageCount
    
    def currentPage(self):
        """Return the current page number in view (starting with 1)."""
        return self._currentPage
    
    def setCurrentPage(self, num):
        """Scrolls to the specified page number (starting with 1).
        
        If the page is already in view, the view is not scrolled, otherwise
        the view is scrolled to center the page. (If the page is larger than 
        the view, the top-left corner is positioned top-left in the view.)
        
        """
        if num > self._pageCount or num < 1 or num == self._currentPage:
            return
        self._currentPage = num
        self.currentPageChanged.emit(num)
        # only move the view if needed
        page = self._pageLayout[num-1]
        m = self._pageLayout.margin
        diff = self.offsetToEnsureVisible(page.geometry().adjusted(-m, -m, m, m))
        if diff:
            if self.kineticPagingEnabled and self.kineticScrollingEnabled:
                # during the scrolling the page number should not be updated.
                self._scrollingToPage = True
                self.kineticScrollBy(diff)
            else:
                self.scrollBy(diff)
    
    def gotoNextPage(self):
        """Convenience method to go to the next page."""
        num = self.currentPage()
        if num < self.pageCount():
            self.setCurrentPage(num + 1)
    
    def gotoPreviousPage(self):
        """Convenience method to go to the previous page."""
        num = self.currentPage()
        if num > 1:
            self.setCurrentPage(num - 1)

    def scrollContentsBy(self, dx, dy):
        """Reimplemented to keep track of current page."""
        # if the scroll wasn't initiated by the setCurrentPage() call, check
        # whether the current page number needs to be updated
        if self.pagingOnScrollEnabled and not self._scrollingToPage and self._pageLayout.count() > 0:
            # do nothing if current page is still fully in view
            if self._pageLayout[self._currentPage-1].geometry() not in self.visibleRect():
                # what is the current page number?
                pos = self.viewport().rect().center() - self.layoutPosition()
                p = self._pageLayout.pageAt(pos) or self._pageLayout.nearestPageAt(pos)
                if p:
                    num = self._pageLayout.index(p) + 1
                    if num != self._currentPage:
                        self._currentPage = num
                        self.currentPageChanged.emit(num)
        super().scrollContentsBy(dx, dy)

    def stopScrolling(self):
        """Reimplemented to stop tracking a scroll initiated by setCurrentPage()."""
        super().stopScrolling()
        self._scrollingToPage = False

    def updatePageLayout(self):
        """Reimplemented to also correctly set the number of pages."""
        super().updatePageLayout()
        n = len(self._pageLayout)
        if n != self._pageCount:
            self._pageCount = n
            self.pageCountChanged.emit(n)
            if self._currentPage > n:
                self._currentPage = n
                self.currentPageChanged.emit(n)
            elif self._currentPage < 1:
                self._currentPage = 1
                self.currentPageChanged.emit(1)

    def resizeEvent(self, ev):
        """Reimplemented to keep the current page in view."""
        old, self._scrollingToPage = self._scrollingToPage, True
        super().resizeEvent(ev)
        if self._viewMode and not self._pageLayout.empty():
            # keep current page in view
            page = self._pageLayout[self._currentPage-1]
            if self.visibleRect().center() not in page.geometry():
                m = self._pageLayout.margin
                diff = self.offsetToEnsureVisible(page.geometry().adjusted(-m, -m, m, m))
                if diff:
                    self.scrollBy(diff)
        self._scrollingToPage = old


