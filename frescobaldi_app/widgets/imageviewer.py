# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
A simple scrollarea that can display an image.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *



class ImageViewer(QScrollArea):
    
    fullSizeChanged = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent, alignment=Qt.AlignCenter)
        self._actualsize = True
        self.setWidget(ImageWidget())
        
    def setActualSize(self, enabled):
        if enabled == self._actualsize:
            return
        self.setWidgetResizable(not enabled)
        if enabled:
            self.widget().setActualSize()
        self._actualsize = enabled
        self.fullSizeChanged.emit(enabled)
        
    def setImage(self, image):
        self.widget().image = image
        if self._actualsize:
            self.widget().setActualSize()
        else:
            self.widget().update()


class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.setBackgroundRole(QPalette.Dark)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image = QImage()
    
    def setActualSize(self):
        self.resize(self.image.size())
        
    def paintEvent(self, ev):
        painter = QPainter(self)
        if self.size() == self.image.size():
            painter.drawImage(ev.rect(), self.image, ev.rect())
            return
        s = self.image.size()
        s.scale(self.size(), Qt.KeepAspectRatio)
        r = QRect()
        r.setSize(s)
        r.moveCenter(self.rect().center())
        painter.drawImage(r, self.image, self.image.rect())


