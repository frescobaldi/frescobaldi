# -*- coding: utf-8 -*-
#
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
import itertools
import math

from PyQt5.QtCore import QMargins, QPoint, QPointF, QRect, QSize, Qt

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

    The following instance attributes are used, with these class-level
    defaults::

        zoomFactor = 1.0
        dpiX = 72.0
        dpiY = 72.0
        rotation = Rotate_0
        orientation = Vertical
        alignment = Qt.AlignCenter

    The layout has margins around each page, accessible via pageMargins(), and
    margins around the whole layout, accessible via margins(). Both have class
    level defaults as a tuple, but they are converted to a QMargins object for
    the layout instance when first accessed via the margins() and pageMargins()
    methods::

        _margins = (6, 6, 6, 6)
        _pageMargins = (0, 0, 0, 0)

        spacing = 8             # pixels between pages

        x = 0                   # x, y, width and height are set by update()
        y = 0
        width = 0
        height = 0

        continuousMode = True   # whether to show all pages

    The actual layout is done by a LayoutEngine in the engine attribute.
    After having changed pages, engine or layout attributes, call update() to
    update the layout.

    """

    _margins = (6, 6, 6, 6)
    _pageMargins = (0, 0, 0, 0)
    spacing = 8
    zoomFactor = 1.0
    dpiX = 72.0
    dpiY = 72.0
    rotation = Rotate_0
    orientation = Vertical
    alignment = Qt.AlignCenter

    continuousMode = True
    currentPageSet = 0  # used in non-continuous mode

    _rects = None

    def __bool__(self):
        """Always return True."""
        return True

    def count(self):
        """Return the number of Page instances."""
        return len(self)

    def empty(self):
        """Return True if there are zero pages."""
        return len(self) == 0

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

    def defaultWidth(self, page):
        """Return the default width of the page."""
        if (page.rotation + self.rotation) & 1:
            return page.pageHeight * page.scaleY / page.dpi
        else:
            return page.pageWidth * page.scaleX / page.dpi

    def defaultHeight(self, page):
        """Return the default height of the page."""
        if (page.rotation + self.rotation) & 1:
            return page.pageWidth * page.scaleX / page.dpi
        else:
            return page.pageHeight * page.scaleY / page.dpi

    def widestPage(self):
        """Return the page with the largest default width, if any."""
        if self.count():
            return max(self, key=self.defaultWidth)

    def highestPage(self):
        """Return the page with the largest default height, if any."""
        if self.count():
            return max(self, key=self.defaultHeight)

    def fit(self, size, mode):
        """Fits the layout in the given size (QSize) and ViewMode."""
        self.engine.fit(self, size, mode)

    def zoomsToFit(self):
        """Return True if the layout engine changes the zoomFactor to fit."""
        return self.engine.zoomToFit

    def update(self):
        """Compute the size of all pages and updates their positions.
        Finally set our own size.

        You should call this after having added or deleted pages or after
        having changed the scale, dpi, zoom factor, spacing or margins.

        This function returns True if the total geometry has changed.

        """
        self._rects = None
        self.updatePageSizes()
        if self.count():
            self.engine.updatePagePositions(self)
        geometry = self.computeGeometry()
        changed = self.geometry() != geometry
        self.setGeometry(geometry)
        return changed

    def updatePageSizes(self):
        """Compute the correct size of every Page."""
        for page in self:
            page.computedRotation = (page.rotation + self.rotation) & 3
            page.updateSize(self.dpiX, self.dpiY, self.zoomFactor)

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

        Every count is the number of page sets of that length. The list is
        created by the LayoutEngine.pageSets() method.

        """
        return self.engine.pageSets(self.count())

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


class LayoutEngine:
    """A LayoutEngine takes care of the actual layout process.

    A PageLayout has its LayoutEngine in the `engine` attribute.  Putting this
    functionality in a separate object makes it easier to alter the behaviour
    of a layout without changing all the user-set options and added Pages.

    The default implementation of LayoutEngine puts pages in a horizontal
    or vertical row.

    You can override grid() to implement a different behaviour, and you
    can override pageSets() to get a different behaviour in non-continuous mode.

    If there are multiple rows or columns, every row is as high as the
    highest page it contains, and every column is as wide as its widest page.
    You can set the attributes evenWidths and/or evenHeights to True if you
    want all columns to have the same width, and/or respectively, the rows the
    same height.

    """

    zoomToFit = True        # True means: engine changes the zoomFactor to fit
    orientation = None      # None means: use layout orientation

    evenWidths = False
    evenHeights = False

    def grid(self, layout):
        """Return a three-tuple (ncols, nrows, prepend).

        ncols is the number of columns the layout will contain, nrows the
        number of rows; and prepend if the number of empty positions that the
        layout wants, when the first row has less pages.

        """
        if layout.orientation == Vertical:
            return 1, layout.count(), 0
        else:
            return layout.count(), 1, 0

    def pages(self, layout, ncols, nrows, prepend=0):
        """Yield the layout's pages in a grid: (page, (x, y)).

        If prepend > 0, that number of first grid positions will remain unused.
        This can be used for layouts that have less pages in the first row.

        """
        if (self.orientation or layout.orientation) == Vertical:
            gen = ((col, row) for col in range(ncols) for row in range(nrows))
        else:
            gen = ((col, row) for row in range(nrows) for col in range(ncols))
        if prepend:
            for i in itertools.islice(gen, prepend):
                pass # skip unused positions
        return zip(layout, gen)

    def dimensions(self, layout, ncols, nrows, prepend=0):
        """Return two lists: columnwidths and rowheights.

        The width and height are page dimensions, without page margin.

        """
        colwidths = [0] * ncols
        rowheights = [0] * nrows
        for page, (col, row) in self.pages(layout, ncols, nrows, prepend):
            colwidths[col] = max(colwidths[col], page.width)
            rowheights[row] = max(rowheights[row], page.height)
        if self.evenWidths:
            colwidths = [max(colwidths)] * ncols
        if self.evenHeights:
            rowheights = [max(rowheights)] * nrows
        return colwidths, rowheights

    def updatePagePositions(self, layout):
        """Performs the positioning of the pages. Don't call on empty layout."""
        ncols, nrows, prepend = self.grid(layout)
        colwidths, rowheights = self.dimensions(layout, ncols, nrows, prepend)

        m = layout.margins()
        pm = layout.pageMargins()
        pmh = pm.left() + pm.right()        # horizontal page margin
        pmv = pm.top() + pm.bottom()        # vertical page margin

        # accumulate for column and row offsets, adding spacing
        xoff = [m.left() + pm.left()] + colwidths[:-1]
        yoff = [m.top() + pm.top()] + rowheights[:-1]
        for i in range(1, ncols):
            xoff[i] += xoff[i-1] + layout.spacing + pmh
        for i in range(1, nrows):
            yoff[i] += yoff[i-1] + layout.spacing + pmv
        # and go for positioning!
        for page, (col, row) in self.pages(layout, ncols, nrows, prepend):
            x, y = util.align(page.width, page.height, colwidths[col], rowheights[row], layout.alignment)
            page.x = xoff[col] + x
            page.y = yoff[row] + y

    def fit(self, layout, size, mode):
        """Called by PageLayout.fit()."""
        if mode and layout.count():
            zoomfactors = []
            if mode & FitWidth:
                zoomfactors.append(self.zoomFitWidth(layout, size.width()))
            if mode & FitHeight:
                zoomfactors.append(self.zoomFitHeight(layout, size.height()))
            layout.zoomFactor = min(zoomfactors)

    def zoomFitWidth(self, layout, width):
        """Return the zoom factor this layout would need to fit in the width.

        This method is called by fit(). The default implementation returns a
        suitable zoom factor for the widest Page.

        """
        m, p = layout.margins(), layout.pageMargins()
        width -= m.left() + m.right() + p.left() + p.right()
        return layout.widestPage().zoomForWidth(width, layout.rotation, layout.dpiX)

    def zoomFitHeight(self, layout, height):
        """Return the zoom factor this layout would need to fit in the height.

        This method is called by fit(). The default implementation returns a
        suitable zoom factor for the highest Page.

        """
        m, p = layout.margins(), layout.pageMargins()
        height -= m.top() + m.bottom() + p.top() + p.bottom()
        return layout.highestPage().zoomForHeight(height, layout.rotation, layout.dpiY)

    def pageSets(self, count):
        """Return a list of (count, length) tuples.

        Every count is the number of page sets of that length. When the layout
        is in non-continuous mode, it displays only a single page set at a time.
        For most layout engines, a page set is just one Page, but for column-
        based layouts other values make sense.

        """
        return [(count, 1)] if count else []


class RowLayoutEngine(LayoutEngine):
    """A layout engine that orders pages in rows.

    Additional instance attributes:

        `pagesPerRow`     = 2, the number of pages to display in a row
        `pagesFirstRow`   = 1, the number of pages to display in the first row
        `fitAllColumns`   = True, whether "fit width" uses all columns

    In non-continuous mode, this layout engine displayes a row of pages
    together. The `orientation` layout attribute is ignored in this layout
    engine.

    """

    pagesPerRow = 2
    pagesFirstRow = 1
    fitAllColumns = True

    orientation = Horizontal    # do not change

    def pageSets(self, count):
        """Return a list of (count, length) tuples respecting our column settings."""
        result = []
        left = count
        if left:
            if self.pagesFirstRow and self.pagesFirstRow != self.pagesPerRow:
                length = min(left, self.pagesFirstRow)
                result.append((1, length))
                left -= length
            if left:
                count, left = divmod(left, self.pagesPerRow)
                if count:
                    result.append((count, self.pagesPerRow))
                if left:
                    # merge result entries with same length
                    if result and result[-1][1] == left:
                        result[-1] == (result[-1][0] + 1, left)
                    else:
                        result.append((1, left))
        return result

    def grid(self, layout):
        """Return (ncols, nrows, prepend).

        Takes into account the pagesPerRow and pagesFirstRow instance
        variables. If desired, prepends empty positions so the first row
        contains less pages than the column width.

        """
        ncols = self.pagesPerRow
        if layout.count() > ncols:
            prepend = (ncols - self.pagesFirstRow) % ncols
        else:
            ncols = layout.count()
            prepend = 0
        nrows = math.ceil((layout.count() + prepend) / ncols)
        return ncols, nrows, prepend

    def zoomFitWidth(self, layout, width):
        """Reimplemented to respect the fitAllColumns setting."""
        if not self.fitAllColumns or self.pagesPerRow == 1 or layout.count() < 2:
            return super().zoomFitWidth(layout, width)
        ncols, nrows, prepend = self.grid(layout)
        m, p = layout.margins(), layout.pageMargins()
        width -= m.left() + m.right() + (p.left() + p.right()) * ncols
        width -= layout.spacing * (ncols - 1)
        if self.evenWidths:
            return super().zoomFitWidth(layout, width // ncols)
        # find the default width of the columns
        cols = [[] for n in range(ncols)]
        for page, (col, row) in self.pages(layout, ncols, nrows, prepend):
            cols[col].append(page)
        # widest page of every column
        widestpages = [max(col, key=layout.defaultWidth) for col in cols]
        totalDefaultWidth = sum(map(layout.defaultWidth, widestpages))
        return min(page.zoomForWidth(
                     width * layout.defaultWidth(page) // totalDefaultWidth,
                     layout.rotation, layout.dpiX)
            for page in widestpages)


class RasterLayoutEngine(LayoutEngine):
    """A layout engine that aligns the pages in a grid.

    This layout does not zoom to fit, but changes the number of columns and rows
    according to the available space. FitBoth is handled like FitWidth.

    """
    zoomToFit = False
    _h = 0
    _w = 0
    _mode = FixedScale

    def fit(self, layout, size, mode):
        """Reimplemented."""
        self._h = size.height()
        self._w = size.width()
        self._mode = mode

    def grid(self, layout):
        """Return a grid that would fit in the layout."""
        m, p = layout.margins(), layout.pageMargins()
        width = self._w - m.left() - m.right()
        height = self._h - m.top() - m.bottom()
        pmh = p.left() + p.right()        # horizontal page margin
        pmv = p.top() + p.bottom()        # vertical page margin

        if self._mode & FitWidth:
            w = layout.widestPage().width + pmh
            ncols = (width + layout.spacing) // (w + layout.spacing)
            if ncols:
                # this will fit, but try more
                for tryncols in range(ncols + 1, layout.count() + 1):
                    trynrows = math.ceil(layout.count() / tryncols)
                    cw, rh = self.dimensions(layout, tryncols, trynrows)
                    # compute width: column widths, spacing and page margins
                    w = sum(cw) + layout.spacing * (tryncols - 1) + pmh * tryncols
                    if w >= width:
                        ncols = tryncols - 1
                        break
                else:
                    ncols = layout.count()
            else:
                ncols = 1   # the minimum
            nrows = math.ceil(layout.count() / ncols)
        elif self._mode & FitHeight:
            h = layout.highestPage().height + pmv
            nrows = (height + layout.spacing) // (h + layout.spacing)
            if nrows:
                # this will fit, but try more
                for trynrows in range(nrows + 1, layout.count() + 1):
                    tryncols = math.ceil(layout.count() / trynrows)
                    cw, rh = self.dimensions(layout, tryncols, trynrows)
                    # compute height: row heights, spacing and page margins
                    h = sum(rh) + layout.spacing * (trynrows - 1) + pmv * trynrows
                    if h >= height:
                        nrows = trynrows - 1
                        break
                else:
                    nrows = layout.count()
            else:
                nrows = 1   # the minimum
            ncols = math.ceil(layout.count() / nrows)
        else:
            ncols = math.ceil(math.sqrt(layout.count()))
            nrows = math.ceil(layout.count() / ncols)
        return ncols, nrows, 0


# install a default layout engine at the class level
PageLayout.engine = LayoutEngine()

