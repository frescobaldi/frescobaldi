# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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

import popplerqt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from . import page

class AbstractLayout(object):
    """Manages page.Page instances with a list-like api."""
    def __init__(self):
        self._pages = []
        self._dpi = (72.0, 72.0)
        self._size = QSize()
        self._margin = 4
        self._spacing = 4
        
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
        
    def __len__(self):
        return len(self._pages)
    
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
            new = list(new)
            self._pages[item] = new
            for page in new:
                self.own(page)
            for page in old:
                self.disown(page)
        else:
            self.disown(self._pages[item])
            self._pages[item] = new
    
    def setSize(self, size):
        """Sets our size. Mainly done after layouting."""
        self._size = size
        
    def size(self):
        """Returns our size as QSize()."""
        return self._size
        
    def setDPI(self, xdpi, ydpi=None):
        """Sets our DPI in X and Y direction. If Y isn't given, uses the X value."""
        self._dpi = xdpi, ydpi or xdpi
        for page in self._pages:
            page.computeSize()
    
    def dpi(self):
        """Returns our DPI as a tuple(XDPI, YDPI)."""
        return self._dpi
        
    def setScale(self, scale):
        """Sets the scale (1.0 == 100%) of all our Pages."""
        for page in self._pages:
            page.setScale(scale)
    
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
        
    def update(self):
        """Implement! Performs the layouting (positions the Pages and adjust our size()."""
        pass
    
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
        
    def load(self, document):
        """Convenience mehod to load all the pages of the given Poppler.Document using page.Page()."""
        self.clear()
        for num in range(document.numPages()):
            self.append(page.Page(document, num))



class Layout(AbstractLayout):
    """A basic layout that shows pages from right to left or top to bottom."""
    def __init__(self):
        super(Layout, self).__init__()
        self._orientation = Qt.Vertical
        
    def setOrientation(self, orientation):
        """Sets our orientation to either horizontal or vertical."""
        self._orientation = orientation
        
    def orientation(self):
        """Returns our orientation (either Qt.Vertical or Qt.Horizontal)."""
        return self._orientation
    
    def setWidth(self, width):
        """Forces all pages the same width. Does not make much sense when orientation() is Qt.Horizontal."""
        pagewidth = width - self._margin * 2
        for page in self:
            page.setWidth(pagewidth)
    
    def setHeight(self, height):
        """Forces all pages the same height. Does not make much sense when orientation() is Qt.Vertical."""
        pageheight = height - self.margin * 2
        for page in self:
            page.setHeight(pageheight)
            
    def update(self):
        """Orders our pages."""
        if self._orientation == Qt.Vertical:
            width = max(page.width() for page in self) + self._margin * 2
            top = self._margin
            for page in self:
                page.setPos(QPoint((width - page.width()) / 2, top))
                top += page.height() + self._spacing
            top += self._margin - self._spacing
            self.setSize(QSize(width, top))
        else:
            height = max(page.height() for page in self) + self._margin * 2
            left = self._margin
            for page in self:
                page.setPos(QPoint(left, (height - page.height()) / 2))
                left += page.width() + self._spacing
            left += self._margin - self._spacing
            self.setSize(QSize(left, height))
            
                
                