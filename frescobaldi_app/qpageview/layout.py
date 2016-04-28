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
        
    def setScale(self, scale):
        """Set our scale (QPointF)."""
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
        """Returns the page that contains the given QPoint."""
        # Specific layouts may use faster algorithms to find the page.
        for page in self:
            if page.rect().contains(point):
                return page
    
    def pagesAt(self, rect):
        """Yields the pages touched by the given QRect."""
        # Specific layouts may use faster algorithms to find the pages.
        for page in self:
            if page.rect().intersects(rect):
                yield page
    
    def update(self):
        """Computes the size of all pages and updates their positions.
        Finally set our own size.
        
        You should call this after having added or deleted pages or after
        having changed the scale, dpi, spacing or margins.
        
        This function returns True if the total size has changed.
        
        """
        self.updatePageSizes()
        self.updatePagePositions()
        return self.computeSize()
    
    def updatePageSizes(self):
        """Computes the correct size of every Page."""
        for page in self:
            page.computeSize(self)

    def updatePagePositions(self):
        """Determines the position of every Page. 
        
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
        """Computes and sets the total size of the layout.
        
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


