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
Manages and positions a group of Page instances.
"""


import copy

from PyQt5.QtCore import QPoint, QPointF, QRect, QSize

from .constants import (
    FixedScale,
    FitWidth,
    FitHeight,
    FitBoth,

    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,

    Horizontal,
    Vertical,
)


class AbstractPageLayout(list):
    """Manages page.Page instances with a list-like api.

    You can iterate over the layout itself, which yields all Page instances.

    The following instance attributes are used, with these defaults:

        margin = 4
        spacing = 8
        zoomFactor = 1.0
        dpiX = 72.0
        dpiY = 72.0
        rotation = Rotate_0
        width = 0
        height = 0

    After having changes pages or layout attributes, call update() to update
    the layout.

    """

    margin = 4
    spacing = 8
    zoomFactor = 1.0
    dpiX = 72.0
    dpiY = 72.0
    rotation = Rotate_0
    width = 0
    height = 0

    def __bool__(self):
        """Always return True."""
        return True

    def count(self):
        """Return the number of Page instances."""
        return len(self)

    def empty(self):
        """Return True if there are zero pages."""
        return len(self) == 0

    def copy(self):
        """Return a copy of this layout with copies of all the pages."""
        layout = copy.copy(self)
        layout[:] = (p.copy() for p in self)
        return layout

    def setSize(self, size):
        """Set our size. Normally done after layout by computeSize()."""
        self.width = size.width()
        self.height = size.height()

    def size(self):
        """Return our size as QSize()."""
        return QSize(self.width, self.height)

    def pageAt(self, point):
        """Return the page that contains the given QPoint."""
        # Specific layouts may use faster algorithms to find the page.
        for page in self:
            if page.rect().contains(point):
                return page

    def pagesAt(self, r):
        """Yield the pages touched by the given QRect or QRegion."""
        # Specific layouts may use faster algorithms to find the pages.
        for page in self:
            if r.intersects(page.rect()):
                yield page

    def widestPage(self):
        """Return the widest page, if any.

        Uses the page's natural width and its scale in X-direction.

        """
        if self.count():
            def key(page):
                psize = page.pageSize()
                if (page.rotation + self.rotation) & 1:
                    return psize.height() * page.scaleY
                else:
                    return psize.width() * page.scaleX
            return max(self, key=key)

    def highestPage(self):
        """Return the highest page, if any.

        Uses the page's natural height and its scale in Y-direction.

        """
        if self.count():
            def key(page):
                psize = page.pageSize()
                if (page.rotation + self.rotation) & 1:
                    return psize.width() * page.scaleX
                else:
                    return psize.height() * page.scaleY
            return max(self, key=key)

    def fit(self, size, mode):
        """Fits the layout in the given size (QSize) and ViewMode."""
        if mode and self.count():
            zoomfactors = []
            if mode & FitWidth:
                zoomfactors.append(self.zoomFitWidth(size.width()))
            if mode & FitHeight:
                zoomfactors.append(self.zoomFitHeight(size.height()))
            self.zoomFactor = min(zoomfactors)

    def zoomFitWidth(self, width):
        """Return the zoom factor this layout would need to fit in the width.

        This method is called by fit(). The default implementation returns a
        suitable zoom factor for the widest Page.

        """
        return self.widestPage().zoomForWidth(self, width - self.margin * 2)

    def zoomFitHeight(self, height):
        """Return the zoom factor this layout would need to fit in the height.

        This method is called by fit(). The default implementation returns a
        suitable zoom factor for the highest Page.

        """
        return self.highestPage().zoomForHeight(self, height - self.margin * 2)

    def update(self):
        """Compute the size of all pages and updates their positions.
        Finally set our own size.

        You should call this after having added or deleted pages or after
        having changed the scale, dpi, zoom factor, spacing or margins.

        This function returns True if the total size has changed.

        """
        self.updatePageSizes()
        self.updatePagePositions()
        return self.computeSize()

    def updatePageSizes(self):
        """Compute the correct size of every Page."""
        for page in self:
            page.updateSizeFromLayout(self)

    def updatePagePositions(self):
        """Determine the position of every Page.

        You should implement this method to perform a meaningful layout, which
        means setting the position of all the pages. This positions should
        respect the margin (and preferably also the spacing).

        """
        top = self.margin
        for page in self:
            page.x = self.margin
            page.y = top
            top += page.height
            top += self.spacing

    def computeSize(self):
        """Compute and set the total size of the layout.

        In most cases the implementation of this method is sufficient: it
        computes the bounding rectangle of all Pages and adds the margin.

        True is returned if the total size has changed.

        """
        r = QRect()
        for page in self:
            r |= page.rect()
        m = self.margin
        size = r.adjusted(-m, -m, m, m).size()
        changed = self.size() != size
        self.setSize(size)
        return changed



class PageLayout(AbstractPageLayout):
    """A basic layout that shows pages from right to left or top to bottom.

    Additional instance attribute:

        `orientation`: Horizontal or Vertical (default)

    """
    orientation = Vertical

    def updatePagePositions(self):
        """Order our pages."""
        if self.orientation == Vertical:
            width = max((p.width for p in self), default=0) + self.margin * 2
            top = self.margin
            for page in self:
                page.x = (width - page.width) / 2
                page.y = top
                top += page.height + self.spacing
        else:
            height = max((p.height for p in self), default=0) + self.margin * 2
            left = self.margin
            for page in self:
                page.x = left
                page.y = (height - page.height) / 2
                left += page.width + self.spacing


class RowPageLayout(AbstractPageLayout):
    """A layout that orders pages in rows.

    Additional instance attributes:

        `pagesPerRow`     = 2, the number of pages to display in a row
        `pagesFirstRow`   = 1, the number of pages to display in the first row
        `fitAllColumns`   = True, whether "fit width" uses all columns

    """

    pagesPerRow = 2
    pagesFirstRow = 1
    fitAllColumns = True

    def zoomFitWidth(self, width):
        """Reimplemented to respect the fitAllColumns setting."""
        width -= self.margin * 2
        if self.fitAllColumns:
            ncols = min(self.pagesPerRow, self.count())
            width = (width - self.spacing * (ncols - 1)) // ncols
        return self.widestPage().zoomForWidth(self, width)

    def updatePagePositions(self):
        """Reimplemented to perform our positioning algorithm."""
        pages = list(self)
        cols = self.pagesPerRow
        if len(pages) > cols:
            ## prepend empty places if the first row should display less pages
            pages[0:0] = [None] * ((cols - self.pagesFirstRow) % cols)
        else:
            cols = len(pages)

        col_widths = []
        col_offsets = []
        offset = self.margin
        for col in range(cols):
            width = max(p.width for p in pages[col::cols] if p)
            col_widths.append(width)
            col_offsets.append(offset)
            offset += width + self.spacing

        top = self.margin
        for row in (pages[i:i + cols] for i in range(0, len(pages), cols or 1)):
            height = max(p.height for p in row if p)
            for n, page in enumerate(row):
                if page:
                    page.x = col_offsets[n] + (col_widths[n] - page.width) // 2
                    page.y = top + (height - page.height) // 2
            top += height + self.spacing


