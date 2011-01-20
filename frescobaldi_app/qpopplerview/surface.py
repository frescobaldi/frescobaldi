#! python



"""
Surface is the widget everything is drawn on.
"""

import weakref


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4


class Surface(QWidget):
    def __init__(self, view):
        super(Surface, self).__init__(view)
        self._view = weakref.ref(view)
        
        p = self.palette()
        p.setBrush(QPalette.Background, p.dark())
        self.setPalette(p)
        
        