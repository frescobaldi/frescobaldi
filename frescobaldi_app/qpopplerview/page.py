#! python

"""
A Page is resposible for drawing a page of a Poppler document
inside a layout.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Page(object):
    def __init__(self, document, pageNumber):
        self._document = document
        self._pageNumber = pageNumber
        self._pageSizeF = document.page(pageNumber).pageSizeF()
        self._rect = QRect()
        self._layout = lambda: None
        
    def document(self):
        return self._document
        
    def pageNumber(self):
        return self._pageNumber
        
    def layout(self):
        return self._layout()
    
    def setLayout(self, layout):
        if self not in layout:
            layout.addPage(self)
            
    def rect(self):
        return self._rect
    
    def size(self):
        return self._rect.size()
    
    def setSize(self, size):
        self._rect.setSize(size)
        
    def pos(self):
        return self._rect.topLeft()
    
    def setPos(self, point):
        self._rect.setTopLeft(point)
    
    def setDPI(self, xres, yres=None):
        if yres is None:
            yres = xres
        x = int(round(self._pageSizeF.width() * xres / 72.0))
        y = int(round(self._pageSizeF.height() * yres / 72.0))
        self.setSize(QSize(x, y))
        
    def paint(self, painter, rect):
        update_rect = rect & self.rect()
        if not update_rect.isValid():
            return
        image = cache.image(self._document, self._pageNumber, self.size())
        if image:
            image_rect = QRect(update_rect.topLeft() - self.rect().topLeft(), ur.size())
            painter.drawImage(update_rect, image, image_rect)
        else:
            painter.fillRect(update_rect, QApplication.palette().background().color())


        