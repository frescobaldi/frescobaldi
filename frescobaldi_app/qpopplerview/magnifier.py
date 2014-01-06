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
The Magnifier magnifies a part of the displayed Poppler document.
"""

import weakref

from PyQt4.QtCore import QPoint, QRect
from PyQt4.QtGui import QPainter, QRegion, QWidget

from . import cache


class Magnifier(QWidget):
    """A Magnifier is added to a Surface with surface.setMagnifier().
    
    It is shown when a mouse button is pressed together with a modifier
    (by default Ctrl, see surface.py).
    
    Its size can be changed with resize() and the scale (defaulting to 4.0)
    with setScale().
    
    """
    def __init__(self, parent = None):
        super(Magnifier, self).__init__(parent)
        self._page= None
        self.setScale(4.0)
        self.resize(250, 250)
        self.hide()
        
    def moveCenter(self, pos):
        """Called by the surface, centers the widget on the given QPoint."""
        r = self.geometry()
        r.moveCenter(pos)
        self.setGeometry(r)
    
    def setScale(self, scale):
        """Sets the scale, relative to the 100% size of a Page.
        
        Uses the dpi() from the layout (pageLayout()) of the surface.
        
        """
        self._scale = scale
        self.update()
    
    def scale(self):
        """Returns the scale, defaulting to 4.0 (=400%)."""
        return self._scale
    
    def resizeEvent(self, ev):
        """Called on resize, sets our circular mask."""
        self.setMask(QRegion(self.rect(), QRegion.Ellipse))
        
    def paintEvent(self, ev):
        """Called when paint is needed, finds out which page to magnify."""
        layout = self.parent().pageLayout()
        pos = self.geometry().center()
        page = layout.pageAt(pos)
        if not page:
            return
        pagePos = pos - page.pos()
        
        newPage = Page(page, self._scale)
        if newPage != self._page:
            if self._page:
                self._page.magnifier = None
            self._page = newPage
            self._page.magnifier = self
        
        relx = pagePos.x() / float(page.width())
        rely = pagePos.y() / float(page.height())
        
        image = cache.image(self._page)
        img_rect = QRect(self.rect())
        if not image:
            cache.generate(self._page)
            image = cache.image(self._page, False)
            if image:
                img_rect.setWidth(self.width() * image.width() / self._page.width())
                img_rect.setHeight(self.height() * image.height() / self._page.height())
        if image:
            img_rect.moveCenter(QPoint(relx * image.width(), rely * image.height()))
            QPainter(self).drawImage(self.rect(), image, img_rect)


class Page(object):
    """A data structure describing a Page like page.Page.
    
    Has the methods the cache needs to create, store and find images
    for our magnifier.
    
    """
    def __init__(self, page, scale):
        """Creates Page, based on the page.Page object and the scale."""
        dpix, dpiy = page.layout().dpi()
        size = page.pageSize()
        self._document = weakref.ref(page.document())
        self._pageNumber = page.pageNumber()
        self._width = size.width() * dpix * scale / 72.0
        self._height = size.height() * dpiy * scale / 72.0
        self._rotation = page.rotation()
        self.magnifier = None
        
    def __eq__(self, other):
        return (
            self._document() == other._document() and
            self._pageNumber == other._pageNumber and
            self._width == other._width and
            self._height == other._height and
            self._rotation == other._rotation
        )

    def document(self):
        return self._document()
    
    def pageNumber(self):
        return self._pageNumber
    
    def width(self):
        return self._width
    
    def height(self):
        return self._height
    
    def rotation(self):
        return self._rotation
    
    def update(self):
        if self.magnifier:
            self.magnifier.update()

