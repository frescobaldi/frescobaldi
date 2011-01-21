#! python

"""
A Page is resposible for drawing a page of a Poppler document
inside a layout.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Page(object):
    def __init__(self, document, pageNumber):
        self._pageNumber = pageNumber
        self._document = document
        self._page = document.page(pageNumber)
        
        self._rect = QRect()
        
    def document(self):
        return self._document
        
    def pageNumber(self):
        return self._pageNumber
        
    def rect(self):
        return self._rect
        
    def paint(self, painter, rect):
        update_rect = rect & self.rect()
        if not update_rect.isValid():
            return
        image = cache.image(self._document, self._rect.size())
        if image:
            image_rect = QRect(update_rect.topLeft() - self.rect().topLeft(), ur.size())
        
        