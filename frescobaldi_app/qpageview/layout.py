# This file is part of the qpageview package.
#
# Copyright (c) 2010 - 2019 by Wilbert Berendsen
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
import math

from PyQt5.QtCore import QMargins, QPoint, QPointF, QRect, QSize

from . import rectangles
from . import util
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


class PageRects(rectangles.Rectangles):
    def get_coords(self, page):
        return page.geometry().getCoords()


class PageLayout(util.Rectangular, list):
    """Manages page.Page instances with a list-like api.

    You can iterate over the layout itself, which yields all Page instances.

    The following instance attributes are used, with these class-level defaults:

        zoomFactor = 1.0
        dpiX = 72.0
        dpiY = 72.0
        rotation = Rotate_0
        orientation = Vertical

    The layout has margins around each page, accessible via pageMargins(), and
    margins around the whole layout, accessible via margins(). Both have class
    level defaults as a tuple, but they are converted to a QMargins object for
    the layout instance when first accessed via the margins() and pageMargins()
    methods.
        
        _margins = (6, 6, 6, 6)
        _pageMargins = (0, 0, 0, 0)
        
        spacing = 8             # pixels between pages

        x = 0                   # x, y, width and height are set by update()
        y = 0
        width = 0
        height = 0

        continuousMode = True   # whether to show all pages
        pagesPerSet = 1         # if not, how many pages per set
        pagesFirstSet = 0       # how many pages in first set
        currentPageSet = 0      # which page set to display

    After having changed pages or layout attributes, call update() to update
    the layout.

    """

    _margins = (6, 6, 6, 6)
    _pageMargins = (0, 0, 0, 0)
    spacing = 8
    zoomFactor = 1.0
    dpiX = 72.0
    dpiY = 72.0
    rotation = Rotate_0
    orientation = Vertical

    continuousMode = True
    pagesPerSet = 1
    pagesFirstSet = 0
    currentPageSet = 0

    _rects = None

    zoomToFit = True    # set to False in layout subclasses that do not zoom to fit

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

    def setMargins(self, margins):
        """Sets our margins to a QMargins object."""
        self._m = margins

    def margins(self):
        """Return our margins as a QMargins object, intialized from _margins"""
        try:
            return self._m
        except AttributeError:
            self._m = QMargins(*self._margins)
            return self._m
    
    def setPageMargins(self, margins):
        """Sets our page margins to a QMargins object."""
        self._pm = margins

    def pageMargins(self):
        """Return our page margins as a QMargins object, intialized from _pageMargins"""
        try:
            return self._pm
        except AttributeError:
            self._pm = QMargins(*self._pageMargins)
            return self._pm
    
    def _pageRects(self):
        """(Internal) Return the PageRects object for quickly finding pages."""
        if self._rects:
            return self._rects
        r = self._rects = PageRects(self.displayPages())
        return r

    def pageAt(self, point):
        """Return the page that contains the given QPoint.

        If the point is not on any page, None is returned.

        """
        for page in self._pageRects().at(point.x(), point.y()):
            return page

    def pagesAt(self, rect):
        """Yield the pages touched by the given QRect.

        The pages are in undefined order.

        """
        for page in self._pageRects().intersecting(*rect.getCoords()):
            yield page

    def nearestPageAt(self, point):
        """Return the page at the shortest distance from the given point.

        The returned page does not contain the point. (Use pageAt() for that.)
        If there are no pages outside the point, None is returned.

        """
        return self._pageRects().nearest(point.x(), point.y())

    def widestPage(self):
        """Return the widest page, if any.

        Uses the page's natural width and its scale in X-direction.

        """
        if self.count():
            def key(page):
                if (page.rotation + self.rotation) & 1:
                    return page.pageHeight * page.scaleY / page.dpi
                else:
                    return page.pageWidth * page.scaleX / page.dpi
            return max(self, key=key)

    def highestPage(self):
        """Return the highest page, if any.

        Uses the page's natural height and its scale in Y-direction.

        """
        if self.count():
            def key(page):
                if (page.rotation + self.rotation) & 1:
                    return page.pageWidth * page.scaleX / page.dpi
                else:
                    return page.pageHeight * page.scaleY / page.dpi
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
        m, p = self.margins(), self.pageMargins()
        width -= m.left() + m.right() + p.left() + p.right()
        return self.widestPage().zoomForWidth(width, self.rotation, self.dpiX)

    def zoomFitHeight(self, height):
        """Return the zoom factor this layout would need to fit in the height.

        This method is called by fit(). The default implementation returns a
        suitable zoom factor for the highest Page.

        """
        m, p = self.margins(), self.pageMargins()
        height -= m.top() + m.bottom() + p.top() + p.bottom()
        return self.highestPage().zoomForHeight(height, self.rotation, self.dpiY)

    def update(self):
        """Compute the size of all pages and updates their positions.
        Finally set our own size.

        You should call this after having added or deleted pages or after
        having changed the scale, dpi, zoom factor, spacing or margins.

        This function returns True if the total geometry has changed.

        """
        self._rects = None
        self.updatePageSizes()
        self.updatePagePositions()
        geometry = self.computeGeometry()
        changed = self.geometry() != geometry
        self.setGeometry(geometry)
        return changed

    def updatePageSizes(self):
        """Compute the correct size of every Page."""
        for page in self:
            page.computedRotation = (page.rotation + self.rotation) & 3
            page.updateSize(self.dpiX, self.dpiY, self.zoomFactor)

    def updatePagePositions(self):
        """Determine the position of every Page.

        You can reimplement this method to perform a different layout, which
        means setting the position of all the pages. These positions should
        respect the margins(), pageMargins(), spacing and if possible the
        orientation.

        """
        m, pm = self.margins(), self.pageMargins()
        if self.orientation == Vertical:
            width = max((p.width for p in self), default=0)
            width += m.left() + m.right() + pm.left() + pm.right()
            top = m.top()
            for page in self:
                top += pm.top()
                page.x = (width - page.width) / 2
                page.y = top
                top += page.height + pm.bottom() + self.spacing
        else:
            height = max((p.height for p in self), default=0)
            height += m.top() + m.bottom() + pm.top() + pm.bottom()
            left = m.left()
            for page in self:
                left += pm.left()
                page.x = left
                page.y = (height - page.height) / 2
                left += page.width + pm.right() + self.spacing

    def computeGeometry(self):
        """Return the total geometry (position and size) of the layout.

        In most cases the implementation of this method is sufficient: it
        computes the bounding rectangle of all Pages and adds the margin.

        """
        r = QRect()
        for page in self.displayPages():
            r |= page.geometry()
        return r + self.margins() + self.pageMargins()

    def pos2offset(self, pos):
        """Return a three-tuple (index, x, y).

        The index refers to a page in the layout, or nowhere if -1. The x and y
        refer to a spot on the page (or layout if empty) in the range 0..1.
        You can use it to store a certain position and restore it after
        changing the zoom e.g.

        """
        page = self.pageAt(pos) or self.nearestPageAt(pos)
        if page:
            pos = pos - page.pos()
            w = page.width
            h = page.height
            i = self.index(page)
        else:
            w = self.width
            h = self.height
            i = -1
        x = pos.x() / w
        y = pos.y() / h
        return (i, x, y)

    def offset2pos(self, offset):
        """Return the pos on the layout for the specified offset.

        The offset is a three-tuple like returned by pos2offset().

        """
        i, x, y = offset
        if i < 0 or i >= len(self):
            pos = QPoint(0, 0)
            w = self.width
            h = self.height
        else:
            page = self[i]
            pos = page.pos()
            w = page.width
            h = page.height
        return pos + QPoint(round(x * w), round(y * h))

    def displayPages(self):
        """Return the pages that are to be displayed."""
        return self[self.currentPageSetSlice()]

    def currentPageSetSlice(self):
        """Return a slice object describing the current page set."""
        if not self.continuousMode:
            num = self.currentPageSet
            count = self.pageSetCount()
            # make sure a valid slice is returned
            if num and num >= count:
                num = self.currentPageSet = count - 1
            p = 0
            s = 0
            for count, length in self.pageSets():
                if p + count <= num:
                    p += count
                    s += count * length
                    continue
                count = num - p
                s += count * length
                return slice(s, s + length)
        return slice(0, self.count())
        
    def pageSets(self):
        """Return a list of (count, length) tuples.

        Every count is the number of page sets of that length. The sum of all
        (count * length) should be the total length of the layout. If the layout
        is empty, an empty list is returned.

        The default implementation reads the pagesFirstSet and pagesPerSet
        attributes, and returns at most three tuples.

        All other pageSet methods use the result of this method for their
        computations.

        """
        result = []
        left = self.count()
        if left:
            if self.pagesFirstSet and self.pagesFirstSet != self.pagesPerSet:
                length = min(left, self.pagesFirstSet)
                result.append((1, length))
                left -= length
            if left:
                count, left = divmod(left, self.pagesPerSet)
                if count:
                    result.append((count, self.pagesPerSet))
                if left:
                    # merge result entries with same length
                    if result and result[-1][1] == left:
                        result[-1] == (result[-1][0] + 1, left)
                    else:
                        result.append((1, left))
        return result

    def pageSetCount(self):
        """Return the number of page sets."""
        return sum(count for count, length in self.pageSets())

    def pageSet(self, index):
        """Return the page set containing page at index."""
        s = 0   # the index at the start of the last page set
        p = 0   # the page set
        for count, length in self.pageSets():
            if s + count * length < index:
                s += count * length
                p += count
                continue
            return p + (index - s) // length
        return 0    # happens with empty layout


class RowPageLayout(PageLayout):
    """A layout that orders pages in rows.

    Additional instance attributes:

        `pagesPerRow`     = 2, the number of pages to display in a row
        `pagesFirstRow`   = 1, the number of pages to display in the first row
        `fitAllColumns`   = True, whether "fit width" uses all columns

    The `pagesFirstSet` and `pagesPerSet` instance attributes are changed to
    properties that automatically use the respective values of pagesFirstRow
    and pagesPerRow.
    
    The `orientation` attribute is ignored in this layout.

    """

    pagesPerRow = 2
    pagesFirstRow = 1
    fitAllColumns = True

    @property
    def pagesPerSet(self):
        return self.pagesPerRow

    @property
    def pagesFirstSet(self):
        return self.pagesFirstRow

    def zoomFitWidth(self, width):
        """Reimplemented to respect the fitAllColumns setting."""
        m, p = self.margins(), self.pageMargins()
        width -= m.left() + m.right() + p.left() + p.right()
        if self.fitAllColumns:
            ncols = min(self.pagesPerRow, self.count())
            width = (width - self.spacing * (ncols - 1)) // ncols
        return self.widestPage().zoomForWidth(width, self.rotation, self.dpiX)

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
        offset = self.margins().left()
        for col in range(cols):
            offset += self.pageMargins().left()
            width = max(p.width for p in pages[col::cols] if p)
            col_widths.append(width)
            col_offsets.append(offset)
            offset += width + self.spacing + self.pageMargins().right()

        top = self.margins().top()
        for row in (pages[i:i + cols] for i in range(0, len(pages), cols or 1)):
            top += self.pageMargins().top()
            height = max(p.height for p in row if p)
            for n, page in enumerate(row):
                if page:
                    page.x = col_offsets[n] + (col_widths[n] - page.width) // 2
                    page.y = top + (height - page.height) // 2
            top += height + self.pageMargins().bottom() + self.spacing


class RasterLayout(PageLayout):
    """A layout that aligns the pages in a grid.

    This layout does not zoom to fit, but changes the number of columns and rows
    according to the available space. FitBoth is handled like FitWidth.

    """
    zoomToFit = False
    _h = 0
    _w = 0
    _mode = FixedScale
    orientation = Horizontal

    def fit(self, size, mode):
        """Reimplemented."""
        self._h = size.height()
        self._w = size.width()
        self._mode = mode

    def updatePagePositions(self):
        """Reimplemented."""
        if self.empty():
            return
        m = self.margins()
        pm = self.pageMargins()
        width = self._w - m.left() - m.right()
        height = self._h - m.top() - m.bottom()
        if self._mode & FitHeight:
            h = self.highestPage().height + pm.top() + pm.bottom()
            nrows = (height + self.spacing) // (h + self.spacing)
            if nrows:
                # this will fit, but try more
                for trynrows in range(nrows + 1, self.count() + 1):
                    tryncols = math.ceil(self.count() / trynrows)
                    cw, rh = self.rasterDimensions(tryncols, trynrows)
                    # compute height: row heights, spacing and page margins
                    h = sum(rh) + self.spacing * (trynrows - 1) + (pm.top() + pm.bottom()) * trynrows
                    if h >= height:
                        nrows = trynrows - 1
                        break
                else:
                    nrows = self.count()
            else:
                nrows = 1   # the minimum
            ncols = math.ceil(self.count() / nrows)
        elif self._mode & FitWidth:
            w = self.widestPage().width + pm.left() + pm.right()
            ncols = (width + self.spacing) // (w + self.spacing)
            if ncols:
                # this will fit, but try more
                for tryncols in range(ncols + 1, self.count() + 1):
                    trynrows = math.ceil(self.count() / tryncols)
                    cw, rh = self.rasterDimensions(tryncols, trynrows)
                    # compute width: column widths, spacing and page margins
                    w = sum(cw) + self.spacing * (tryncols - 1) + (pm.left() + pm.right()) * tryncols
                    if w >= width:
                        ncols = tryncols - 1
                        break
                else:
                    ncols = self.count()
            else:
                ncols = 1   # the minimum
            nrows = math.ceil(self.count() / ncols)
        else:
            # order in a square
            ncols = math.ceil(math.sqrt(self.count()))
            nrows = math.ceil(self.count() / ncols)
        # determine column widths and row heights
        colwidths, rowheights = self.rasterDimensions(ncols, nrows)
        # accumulate for column and row offsets, adding spacing
        xoff = [0] + colwidths[:-1]
        yoff = [0] + rowheights[:-1]
        for i in range(1, ncols):
            xoff[i] += xoff[i-1] + self.spacing + pm.left() + pm.right()
        for i in range(1, nrows):
            yoff[i] += yoff[i-1] + self.spacing + pm.top() + pm.bottom()
        # and go for positioning!
        sx = m.left() + pm.left()
        sy = m.top() + pm.top()
        for page, (col, row) in self.pagesInRaster(ncols, nrows):
            x = sx + xoff[col] + colwidths[col] // 2
            y = sy + yoff[row] + rowheights[row] // 2
            g = page.geometry()
            g.moveCenter(QPoint(x, y))
            page.setGeometry(g)

    def pagesInRaster(self, ncols, nrows):
        """Yield page, (col, row) for all pages, according to the orientation."""
        def gen():
            if self.orientation == Vertical:
                for col in range(ncols):
                    for row in range(nrows):
                        yield col, row
            else:
                for row in range(nrows):
                    for col in range(ncols):
                        yield col, row
        return zip(self, gen())

    def rasterDimensions(self, ncols, nrows):
        """Return two lists: columnwidths and rowheights.

        The width and height are page dimensions, without page margin.

        """
        # determine column widths and row heights
        rowheights = [0] * nrows
        colwidths = [0] * ncols
        for page, (col, row) in self.pagesInRaster(ncols, nrows):
            rowheights[row] = max(rowheights[row], page.height)
            colwidths[col] = max(colwidths[col], page.width)
        return colwidths, rowheights
