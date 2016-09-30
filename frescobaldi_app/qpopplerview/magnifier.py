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

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QColor, QPainter, QPen, QRegion
from PyQt5.QtWidgets import QWidget

from . import cache


class Magnifier(QWidget):
    """A Magnifier is added to a Surface with surface.setMagnifier().
    
    It is shown when a mouse button is pressed together with a modifier
    (by default Ctrl, see surface.py).
    
    Its size can be changed with resize() and the scale (defaulting to 4.0)
    with setScale().
    
    """
    
    # Maximum extra zoom above the View.MAX_ZOOM
    MAX_EXTRA_ZOOM = 1.25
    
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
        r.translate(self.parent().surface().pos())
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
        layout = self.parent().surface().pageLayout()
        pos = self.geometry().center() - self.parent().surface().pos()
        page = layout.pageAt(pos)
        if not page:
            return
        pagePos = pos - page.pos()
        
        max_zoom = self.parent().surface().view().MAX_ZOOM * self.MAX_EXTRA_ZOOM
        newPage = Page(page, min(max_zoom, self._scale * page.scale()))
        if not newPage.same_page(self._page):
            if self._page:
                self._page.magnifier = None
            self._page = newPage
            self._page.magnifier = self
        
        relx = pagePos.x() / float(page.width())
        rely = pagePos.y() / float(page.height())
        
        image = cache.image(self._page)
        img_rect = QRect(self.rect())
        img_rect.setSize( img_rect.size()*self._page._retinaFactor );
        
        if not image:
            cache.generate(self._page)
            image = cache.image(self._page, False)
            if image:
                img_rect.setWidth(img_rect.width() * image.width() / self._page.physWidth())
                img_rect.setHeight(img_rect.height() * image.height() / self._page.physHeight())
        if image:
            img_rect.moveCenter(QPoint(relx * image.width(), rely * image.height()))
            p = QPainter(self)
            p.drawImage(self.rect(), image, img_rect)
            p.setRenderHint(QPainter.Antialiasing, True)
            p.setPen(QPen(QColor(192, 192, 192, 128), 6))
            p.drawEllipse(self.rect().adjusted(2, 2, -2, -2))


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
        self._retinaFactor = page._retinaFactor
        self._rotation = page.rotation()
        self.magnifier = None
        
    def same_page(self, other):
        return (
            other is not None and
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

    def physWidth(self):
        return self._width*self._retinaFactor

    def physHeight(self):
        return self._height*self._retinaFactor
    
    def rotation(self):
        return self._rotation
    
    def update(self):
        if self.magnifier:
            self.magnifier.update()

