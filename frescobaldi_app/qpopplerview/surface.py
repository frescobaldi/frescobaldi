#! python



"""
Surface is the widget everything is drawn on.
"""

import weakref


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4

from . import layout


class Surface(QWidget):
    def __init__(self, view):
        super(Surface, self).__init__(view)
        self._view = weakref.ref(view)
        self._pageLayout = layout.Layout()
        
        p = self.palette()
        p.setBrush(QPalette.Background, p.dark())
        self.setPalette(p)
        self.setAutoFillBackground(True)
        
    def pageLayout(self):
        return self._pageLayout
        
    def setPageLayout(self, layout):
        self._pageLayout = layout
        
    def updateLayout(self):
        """Conforms ourselves to our layout (that must already be updated.)"""
        self.resize(self._pageLayout.size())
        self.update()
        
    def paintEvent(self, ev):
        painter = QPainter(self)
        for page in self.pageLayout().pagesAt(ev.rect()):
            page.paint(painter, ev.rect())
    
