# This file is part of the qpopplerview package.
#
# Copyright (c) 2010 - 2014 by Wilbert Berendsen
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
Manages and positions a group of Page instances.
"""

import weakref

from PyQt5.QtCore import QObject, QPoint, QRect, QSize, Qt, pyqtSignal

from . import page
from . import (
    # viewModes:
    FixedScale,
    FitWidth,
    FitHeight,
    FitBoth,
)


class AbstractLayout(QObject):
    """Manages page.Page instances with a list-like api.

    You can iterate over the layout itself, which yields all Page instances.
    You can also iterate over pages(), which only yields the Page instances
    that are visible().

    """

    redraw = pyqtSignal(QRect)
    changed = pyqtSignal()
    scaleChanged = pyqtSignal(float)

    def __init__(self):
        super(AbstractLayout, self).__init__()
        self._pages = []
        self._size = QSize()
        self._margin = 4
        self._spacing = 8
        self._scale = 1.0
        self._scaleChanged = False
        self._dpi = (72, 72)

    def own(self, page):
        """(Internal) Makes the page have ourselves as layout."""
        if page.layout():
            page.layout().remove(page)
        page._layout = weakref.ref(self)
        page.computeSize()

    def disown(self, page):
        """(Internal) Removes ourselves as owner of the page."""
        page._layout = lambda: None

    def append(self, page):
        self.own(page)
        self._pages.append(page)

    def insert(self, position, page):
        self.own(page)
        self._pages.insert(position, page)

    def extend(self, pages):
        for page in pages:
            self.append(page)

    def remove(self, page):
        self._pages.remove(page)
        self.disown(page)

    def pop(self, index=None):
        page = self._pages.pop(index)
        self.disown(page)
        return page

    def clear(self):
        del self[:]

    def count(self):
        return len(self._pages)

    def __len__(self):
        return len(self._pages)

    def __bool__(self):
        return True

    def __contains__(self, page):
        return page in self._pages

    def __getitem__(self, item):
        return self._pages[item]

    def __delitem__(self, item):
        if isinstance(item, slice):
            for page in self._pages[item]:
                self.disown(page)
        else:
            self.disown(self._pages[item])
        del self._pages[item]

    def __setitem__(self, item, new):
        if isinstance(item, slice):
            old = self._pages[item]
            self._pages[item] = new
            for page in self._pages[item]:
                self.own(page)
            for page in old:
                self.disown(page)
        else:
            self.disown(self._pages[item])
            self._pages[item] = new
            self.own(new)

    def index(self, page):
        """Returns the index at which the given Page can be found in our Layout."""
        return self._pages.index(page)

    def setSize(self, size):
        """Sets our size. Mainly done after layout."""
        self._size = size

    def size(self):
        """Returns our size as QSize()."""
        return self._size

    def width(self):
        """Returns our width."""
        return self._size.width()

    def height(self):
        """Returns our height."""
        return self._size.height()

    def setDPI(self, xdpi, ydpi=None):
        """Sets our DPI in X and Y direction. If Y isn't given, uses the X value."""
        self._dpi = xdpi, ydpi or xdpi
        for page in self:
            page.computeSize()

    def dpi(self):
        """Returns our DPI as a tuple(XDPI, YDPI)."""
        return self._dpi

    def scale(self):
        """Returns the scale (1.0 == 100%)."""
        return self._scale

    def setScale(self, scale):
        """Sets the scale (1.0 == 100%) of all our Pages."""
        if scale != self._scale:
            self._scale = scale
            for page in self:
                page.setScale(scale)
            self._scaleChanged = True

    def setPageWidth(self, width, sameScale=True):
        """Sets the width of all pages.

        If sameScale is True (default), the largest page will be scaled to the given
        width (minus margin).  All pages will then be scaled to that scale.
        If sameScale is False all pages will be scaled individually to the same width.

        """
        if sameScale and any(self.pages()):
            self.setScale(self.widest().scaleForWidth(width))
        else:
            for page in self:
                page.setWidth(width)

    def setPageHeight(self, height, sameScale=True):
        """Sets the height of all pages.

        If sameScale is True (default), the largest page will be scaled to the given
        height (minus margin).  All pages will then be scaled to that scale.
        If sameScale is False all pages will be scaled individually to the same height.

        """
        if sameScale and any(self.pages()):
            self.setScale(self.highest().scaleForWidth(height))
        else:
            for page in self:
                page.setHeight(height)

    def setMargin(self, margin):
        """Sets the margin around the pages in pixels."""
        self._margin = margin

    def margin(self):
        """Returns the margin around the pages in pixels."""
        return self._margin

    def setSpacing(self, spacing):
        """Sets the space between the pages in pixels."""
        self._spacing = spacing

    def spacing(self):
        """Returns the space between the pages in pixels."""
        return self._spacing

    def fit(self, size, mode):
        """Fits the layout in the given ViewMode."""
        if mode and any(self.pages()):
            scales = []
            if mode & FitWidth:
                scales.append(self.scaleFitWidth(size.width()))
            if mode & FitHeight:
                scales.append(self.scaleFitHeight(size.height()))
            self.setScale(min(scales))

    def scaleFitHeight(self, height):
        """Return the scale this layout would need to fit in the height.

        This method is called by fit().
        The default implementation returns a suitable scale for the highest Page.

        """
        return self.highest().scaleForHeight(height - self.margin() * 2)

    def scaleFitWidth(self, width):
        """Return the scale this layout would need to fit in the width.

        This method is called by fit().
        The default implementation returns a suitable scale for the widest Page.

        """
        return self.widest().scaleForWidth(width - self.margin() * 2)

    def update(self):
        """Performs the layout (positions the Pages and adjusts our size)."""
        self.reLayout()
        if self._scaleChanged:
            self.scaleChanged.emit(self._scale)
            self._scaleChanged = False
        self.changed.emit()

    def reLayout(self):
        """This is called by update().

        You must implement this method to position the Pages and adjust our size.
        See Layout for a possible implementation.

        """
        pass

    def updatePage(self, page):
        """Called by the Page when an image has been generated."""
        self.redraw.emit(page.rect())

    def page(self, document, pageNumber):
        """Returns the page (visible or not) from a Poppler.Document with page number.

        Returns None if that page is not available.

        """
        # Specific layouts may use faster algorithms to find the page.
        try:
            page = self[pageNumber]
        except IndexError:
            pass
        else:
            if page.document() == document:
                return page
        for page in self:
            if page.document() == document and page.pageNumber() == pageNumber:
                return page

    def pages(self):
        """Yields our pages that are visible()."""
        for page in self:
            if page.visible():
                yield page

    def pageAt(self, point):
        """Returns the page that contains the given QPoint."""
        # Specific layouts may use faster algorithms to find the page.
        for page in self.pages():
            if page.rect().contains(point):
                return page

    def pagesAt(self, rect):
        """Yields the pages touched by the given QRect."""
        # Specific layouts may use faster algorithms to find the pages.
        for page in self.pages():
            if page.rect().intersects(rect):
                yield page

    def linkAt(self, point):
        """Returns (page, link) if pos points to a Poppler.Link in a Page, else (None, None)."""
        page = self.pageAt(point)
        if page:
            links = page.linksAt(point)
            if links:
                return page, links[0]
        return None, None

    def widest(self):
        """Returns the widest visible page (in its natural page size)."""
        pages = list(self.pages())
        if pages:
            return max(pages, key = lambda p: p.pageSize().width())

    def highest(self):
        """Returns the highest visible page (in its natural page size)."""
        pages = list(self.pages())
        if pages:
            return max(pages, key = lambda p: p.pageSize().height())

    def maxWidth(self):
        """Returns the width of the widest visible page."""
        page = self.widest()
        return page.width() if page else 0

    def maxHeight(self):
        """Returns the height of the highest visible page."""
        page = self.highest()
        return page.height() if page else 0

    def load(self, document):
        """Convenience method to load all the pages of the given Poppler.Document using page.Page()."""
        self.clear()
        for num in range(document.numPages()):
            p = page.Page(document, num)
            p.setScale(self._scale)
            self.append(p)


class Layout(AbstractLayout):
    """A basic layout that shows pages from right to left or top to bottom."""
    def __init__(self):
        super(Layout, self).__init__()
        self._orientation = Qt.Vertical

    def setOrientation(self, orientation):
        """Sets our orientation to either Qt.Vertical or Qt.Horizontal."""
        self._orientation = orientation

    def orientation(self):
        """Returns our orientation (either Qt.Vertical or Qt.Horizontal)."""
        return self._orientation

    def reLayout(self):
        """Orders our pages."""
        if self._orientation == Qt.Vertical:
            width = self.maxWidth() + self._margin * 2
            top = self._margin
            for page in self.pages():
                page.setPos(QPoint((width - page.width()) / 2, top))
                top += page.height() + self._spacing
            top += self._margin - self._spacing
            self.setSize(QSize(width, top))
        else:
            height = self.maxHeight() + self._margin * 2
            left = self._margin
            for page in self.pages():
                page.setPos(QPoint(left, (height - page.height()) / 2))
                left += page.width() + self._spacing
            left += self._margin - self._spacing
            self.setSize(QSize(left, height))


class RowLayout(AbstractLayout):
    """A layout that orders pages in rows."""
    def __init__(self):
        super(RowLayout, self).__init__()
        self._npages = 2
        self._npages_first = 1
        self._fit_width_uses_all_columns = True

    def setPagesPerRow(self, n):
        """Set the number of pages to show per row."""
        self._npages = n

    def pagesPerRow(self):
        """Return the number of pages to show per row."""
        return self._npages

    def setPagesFirstRow(self, n):
        """Set the number of pages to show in the first row."""
        self._npages_first = n

    def pagesFirstRow(self):
        """Return the number of pages to show in the first row."""
        return self._npages_first

    def setFitWidthUsesAllColumns(self, allcols):
        """Set "Fit Width uses all columns" to True or False.

        If True, the FitWidth view mode tries to display all columns in the
        requested width. If False, the widest Page determines the used scale.

        The default setting is True.

        """
        self._fit_width_uses_all_columns = allcols

    def fitFitWidthUsesAllColumns(self):
        """Return whether the Fit Width view mode displays all columns in the
        requested width.

        """
        return self._fit_width_uses_all_columns

    def scaleFitWidth(self, width):
        """Reimplemented to respect the fitFitWidthUsesAllColumns() setting."""
        width -= self.margin() * 2
        if self._fit_width_uses_all_columns:
            ncols = min(self._npages, self.count())
            width = (width - self.spacing() * (ncols - 1)) // ncols
        return self.widest().scaleForWidth(width)

    def reLayout(self):
        pages = list(self.pages())
        cols = self._npages
        if len(pages) > cols:
            ## prepend empty places if the first row should display less pages
            pages[0:0] = [None] * ((cols - self._npages_first) % cols)
        else:
            cols = len(pages)

        col_widths = []
        col_offsets = []
        offset = self._margin
        col = -1
        for col in range(cols):
            width = max(p.width() for p in pages[col::cols] if p)
            col_widths.append(width)
            col_offsets.append(offset)
            offset += width + self._spacing
        total_width = offset + self._margin
        if col != -1:
            total_width -= self._spacing

        top = self._margin
        x = -1
        for row in (pages[i:i + cols] for i in range(0, len(pages), cols or 1)):
            height = max(p.height() for p in row if p)
            for n, page in enumerate(row):
                if page:
                    x = col_offsets[n] + (col_widths[n] - page.width()) // 2
                    y = top + (height - page.height()) // 2
                    page.setPos(QPoint(x, y))
            top += height + self._spacing
        total_height = top + self._margin
        if x != -1:
            total_height -= self._spacing
        self.setSize(QSize(total_width, total_height))


