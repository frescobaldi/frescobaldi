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


class AbstractPageLayout:
    """Manages page.Page instances with a list-like api.
    
    You can iterate over the layout itself, which yields all Page instances.
    
    """
    def __init__(self):
        self._pages = []
        self._size = QSize()
        self._margin = 4
        self._spacing = 8
        self._zoomFactor = 1.0
        self._scale = QPointF(1.0, 1.0)
        self._dpi = QPointF(72, 72)
        self._rotation = Rotate_0
        
    def append(self, page):
        self._pages.append(page)
        
    def insert(self, position, page):
        self._pages.insert(position, page)
    
    def extend(self, pages):
        for page in pages:
            self.append(page)
            
    def remove(self, page):
        self._pages.remove(page)
    
    def pop(self, index=None):
        page = self._pages.pop(index)
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
        del self._pages[item]
    
    def __setitem__(self, item, new):
        self._pages[item] = new
    
    def index(self, page):
        """Return the index at which the given Page can be found in our Layout."""
        return self._pages.index(page)
        
    def setSize(self, size):
        """Set our size. Normally done after layout by computeSize()."""
        self._size = size
        
    def size(self):
        """Return our size as QSize()."""
        return self._size
    
    def width(self):
        """Return our width."""
        return self._size.width()
    
    def height(self):
        """Return our height."""
        return self._size.height()
    
    def setMargin(self, margin):
        """Set the margin around the pages in pixels."""
        self._margin = margin
        
    def margin(self):
        """Return the margin around the pages in pixels."""
        return self._margin
        
    def setSpacing(self, spacing):
        """Sets the space between the pages in pixels."""
        self._spacing = spacing
        
    def spacing(self):
        """Returns the space between the pages in pixels."""
        return self._spacing
        
    def setDpi(self, dpi):
        """Set our DPI (QPointF)"""
        self._dpi = xdpi, ydpi or xdpi
    
    def dpi(self):
        """Return our DPI as a QPointF(XDPI, YDPI)."""
        return self._dpi
    
    def setZoomFactor(self, zoom):
        """Set the zoom factor to enlarge or shrink the pages."""
        self._zoomFactor = zoom
    
    def zoomFactor(self):
        """Return the zoom factor (1.0 by default)."""
        return self._zoomFactor
    
    def setScale(self, scale):
        """Set our scale (QPointF). 
        
        Normally you'd leave the scale at QPointF(1.0, 1.0), but you can use
        it to support displays with non-square pixels, etc.
        
        """
        self._scale = scale
    
    def scale(self):
        """Return our scale (QPointF)."""
        return self._scale
    
    def setRotation(self, rotation):
        """Set the rotation (see .constants) of this layout."""
        self._rotation = rotation
    
    def rotation(self):
        """Return the rotation of this layout."""
        return self._rotation
    
    def pageAt(self, point):
        """Return the page that contains the given QPoint."""
        # Specific layouts may use faster algorithms to find the page.
        for page in self:
            if page.rect().contains(point):
                return page
    
    def pagesAt(self, rect):
        """Yield the pages touched by the given QRect."""
        # Specific layouts may use faster algorithms to find the pages.
        for page in self:
            if page.rect().intersects(rect):
                yield page
    
    def widestPage(self):
        """Return the widest page, if any.
        
        Uses the page's natural width and its scale in X-direction.
        
        """
        if self.count():
            def key(page):
                psize = page.pageSizeF()
                if (page.rotation() + self.rotation()) & 1:
                    return psize.height() * page.scale().y()
                else:
                    return psize.width() * page.scale().x()
            return max(self, key=key)
    
    def highestPage(self):
        """Return the highest page, if any.
        
        Uses the page's natural height and its scals in Y-direction.
        
        """
        if self.count():
            def key(page):
                psize = page.pageSizeF()
                if (page.rotation() + self.rotation()) & 1:
                    return psize.width() * page.scale().x()
                else:
                    return psize.height() * page.scale().y()
            return max(self, key=key)
    
    def fit(self, size, mode):
        """Fits the layout in the given ViewMode."""
        if mode and self._pages:
            zoomfactors = []
            if mode & FitWidth:
                zoomfactors.append(self.zoomFitWidth(size.width()))
            if mode & FitHeight:
                zoomfactors.append(self.zoomFitHeight(size.height()))
            self.setZoomFactor(min(zoomfactors))
    
    def zoomFitWidth(self, width):
        """Return the zoom factor this layout would need to fit in the width.
        
        This method is called by fit(). The default implementation returns a 
        suitable zoom factor for the widest Page.
        
        """
        return self.widestPage().zoomForWidth(self, width - self.margin() * 2)
    
    def zoomFitHeight(self, height):
        """Return the zoom factor this layout would need to fit in the height.
        
        This method is called by fit(). The default implementation returns a 
        suitable zoom factor for the highest Page.
        
        """
        return self.highestPage().zoomForHeight(self, height - self.margin() * 2)
    
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
            page.computeSize(self)

    def updatePagePositions(self):
        """Determine the position of every Page. 
        
        You should implement this method to perform a meaningful layout, which 
        means setting the position of all the pages. This positions should 
        respect the margin (and preferably also the spacing).
        
        """
        top = self._margin
        for page in self:
            page.setPos(QPoint(self._margin, top))
            top += page.height()
            top += self._spacing
    
    def computeSize(self):
        """Compute and set the total size of the layout.
        
        In most cases the implementation of this method is sufficient: it
        computes the bounding rectangle of all Pages and adds the margin.
        
        True is returned if the total size has changed.
        
        """
        r = QRect()
        for page in self:
            r |= page.rect()
        m = self._margin
        size = r.adjusted(-m, -m, m, m).size()
        changed = self._size != size
        self.setSize(size)
        return changed



class PageLayout(AbstractPageLayout):
    """A basic layout that shows pages from right to left or top to bottom."""
    def __init__(self):
        super().__init__()
        self._orientation = Vertical
        
    def setOrientation(self, orientation):
        """Set our orientation to either Vertical or Horizontal."""
        self._orientation = orientation
        
    def orientation(self):
        """Return our orientation (either Vertical or Horizontal)."""
        return self._orientation
    
    def updatePagePositions(self):
        """Order our pages."""
        if self._orientation == Vertical:
            width = max((p.width() for p in self), default=0) + self._margin * 2
            top = self._margin
            for page in self:
                page.setPos(QPoint((width - page.width()) / 2, top))
                top += page.height() + self._spacing
        else:
            height = max((p.height() for p in self), default=0) + self._margin * 2
            left = self._margin
            for page in self:
                page.setPos(QPoint(left, (height - page.height()) / 2))
                left += page.width() + self._spacing


class RowPageLayout(AbstractPageLayout):
    """A layout that orders pages in rows."""
    def __init__(self):
        super().__init__()
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
        requested width. If False, the widest Page determines the used zoom.
        
        The default setting is True.
        
        """
        self._fit_width_uses_all_columns = allcols
    
    def fitFitWidthUsesAllColumns(self):
        """Return whether the Fit Width view mode displays all columns in the
        requested width.
        
        """
        return self._fit_width_uses_all_columns
    
    def zoomFitWidth(self, width):
        """Reimplemented to respect the fitFitWidthUsesAllColumns() setting."""
        width -= self.margin() * 2
        if self._fit_width_uses_all_columns:
            ncols = min(self._npages, self.count())
            width = (width - self.spacing() * (ncols - 1)) // ncols
        return self.widestPage().zoomForWidth(self, width)
        
    def updatePagePositions(self):
        """Reimplemented to perform our positioning algorithm."""
        pages = list(self)
        cols = self._npages
        if len(pages) > cols:
            ## prepend empty places if the first row should display less pages
            pages[0:0] = [None] * ((cols - self._npages_first) % cols)
        else:
            cols = len(pages)
        
        col_widths = []
        col_offsets = []
        offset = self._margin
        for col in range(cols):
            width = max(p.width() for p in pages[col::cols] if p)
            col_widths.append(width)
            col_offsets.append(offset)
            offset += width + self._spacing
        
        top = self._margin
        for row in (pages[i:i + cols] for i in range(0, len(pages), cols or 1)):
            height = max(p.height() for p in row if p)
            for n, page in enumerate(row):
                if page:
                    x = col_offsets[n] + (col_widths[n] - page.width()) // 2
                    y = top + (height - page.height()) // 2
                    page.setPos(QPoint(x, y))
            top += height + self._spacing


