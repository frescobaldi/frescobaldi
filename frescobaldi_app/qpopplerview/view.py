#! python

"""
QPopplerView widget to display PDF documents.
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4

from . import surface


class View(QScrollArea):
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        
        self.setAlignment(Qt.AlignCenter)
        
        p = self.palette()
        p.setBrush(QPalette.Background, p.dark())
        self.setPalette(p)
        
        self.setWidget(surface.Surface(self))
    
    def surface(self):
        """Returns our Surface, the widget drawing the page(s)."""
        return self.widget()
        
    def setDocument(self, document):
        """Opens the given Poppler.Document"""

