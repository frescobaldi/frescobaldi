#! python

"""
A Page is resposible for drawing a page of a Poppler document
inside a layout.
"""

import popplerqt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Page(object):
    def __init__(self, document, pageNumber):
        self._document = document
        self._pageNumber = pageNumber
        self._pageSizeF = document.page(pageNumber).pageSizeF()
        self._rotation = popplerqt4.Poppler.Page.Rotate0
        self._rect = QRect()
        self.setDPI(72.0)
        self._layout = lambda: None
        
    def document(self):
        """Returns the document."""
        return self._document
        
    def pageNumber(self):
        """Returns the page number."""
        return self._pageNumber
        
    def layout(self):
        """Returns the Layout if we are part of one."""
        return self._layout()
    
    def rect(self):
        """Returns our QRect(), with position and size."""
        return self._rect
    
    def size(self):
        """Returns our size."""
        return self._rect.size()
    
    def height(self):
        """Returns our height."""
        return self._rect.height()
        
    def width(self):
        """Returns our width."""
        return self._rect.width()
        
    def pos(self):
        """Returns our position."""
        return self._rect.topLeft()
    
    def setPos(self, point):
        """Sets our position (affects the Layout)."""
        self._rect.setTopLeft(point)
    
    def setDPI(self, xres, yres=None):
        """Sets our dots per inch in x and y direction.
        
        If y is not given, the same value as for x is used.
        
        """
        if yres is None:
            yres = xres
        self._xres = xres
        self._yres = yres
        
        s = self._pageSizeF
        if self._rotation & 1:
            s.transpose()
        x = int(round(s.width() * xres / 72.0))
        y = int(round(s.height() * yres / 72.0))
        self._rect.setSize(QSize(x, y))
    
    def dpi(self):
        """Returns a tuple (xres, yres)."""
        return self._xres, self._yres
        
    def setRotation(self, rotation):
        """Sets our Poppler.Page.Rotation."""
        old, self._rotation = self._rotation, rotation
        if (old ^ rotation) & 1:
            # swap x and y in our size
            s = self._rect.size()
            s.transpose()
            self._rect.setSize(s)
    
    def rotation(self):
        """Returns our rotation."""
        return self._rotation
    
    def setWidth(self, width):
        """Forces our width (influences size() and dpi())."""
        if width != self.width():
            scale = float(width) / self._rect.width()
            xres, yres = self.dpi()
            self.setDPI(xres * scale, yres * scale)

    def setHeight(self, height):
        """Forces our height (influences size() and dpi())."""
        if height != self.height():
            scale = float(height) / self._rect.height()
            xres, yres = self.dpi()
            self.setDPI(xres * scale, yres * scale)
        
    def paint(self, painter, rect):
        update_rect = rect & self.rect()
        if not update_rect:
            return
        image = cache.image(self._document, self._pageNumber, self.size())
        if image:
            image_rect = QRect(update_rect.topLeft() - self.rect().topLeft(), ur.size())
            painter.drawImage(update_rect, image, image_rect)
        else:
            painter.fillRect(update_rect, QApplication.palette().background().color())


        