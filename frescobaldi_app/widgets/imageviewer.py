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

from PyQt4.QtCore import pyqtSignal, QMimeData, QSize, QRect, Qt
from PyQt4.QtGui import (
    QApplication, QDrag, QImage, QPainter, QPalette, QPixmap, QScrollArea,
    QSizePolicy, QWidget)


# internal constants
MOVE = 1
DRAG = 2


class ImageViewer(QScrollArea):
    
    fullSizeChanged = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent, alignment=Qt.AlignCenter)
        self._actualsize = True
        self.setBackgroundRole(QPalette.Dark)
        self.setWidget(ImageWidget(self))
        
    def setActualSize(self, enabled=True):
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
        self.widget().update()


class ImageWidget(QWidget):
    def __init__(self, viewer):
        super(ImageWidget, self).__init__()
        self.viewer = viewer
        self.setBackgroundRole(QPalette.Dark)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image = QImage()
        self._pixmap = None
        self._pixmapsize = None
        self._mode = None
        self._startpos = None
    
    def setActualSize(self):
        self.resize(self.image.size())
        self._pixmap = None
        self._pixmapsize = None
        
    def paintEvent(self, ev):
        painter = QPainter(self)
        if self.size() == self.image.size():
            painter.drawImage(ev.rect(), self.image, ev.rect())
        else:
            s = self.image.size()
            s.scale(self.size(), Qt.KeepAspectRatio)
            r = QRect()
            r.setSize(s)
            r.moveCenter(self.rect().center())
            painter.drawPixmap(r, self.pixmap(s))

    def pixmap(self, size):
        if self._pixmapsize == size:
            return self._pixmap
        self._pixmap = QPixmap.fromImage(self.image.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self._pixmapsize = size
        return self._pixmap

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            if ev.modifiers() & Qt.ControlModifier:
                self._mode = MOVE
            else:
                self._mode = DRAG
            self._startpos = ev.globalPos()
    
    def mouseMoveEvent(self, ev):
        diff = self._startpos - ev.globalPos()
        if self._mode == MOVE:
            self._startpos = ev.globalPos()
            h = self.viewer.horizontalScrollBar()
            v = self.viewer.verticalScrollBar()
            h.setValue(h.value() + diff.x())
            v.setValue(v.value() + diff.y())
        elif self._mode == DRAG and diff.manhattanLength() >= QApplication.startDragDistance():
            self.startDrag()
    
    def mouseReleaseEvent(self, ev):
        mode, self._mode = self._mode, None
        if (ev.button() == Qt.LeftButton and
                mode == DRAG and ev.globalPos() == self._startpos):
            self.viewer.setActualSize(not self.viewer._actualsize)
    
    def startDrag(self):
        data = QMimeData()
        data.setImageData(self.image)
        drag = QDrag(self.viewer)
        drag.setMimeData(data)
        image = self.image
        if max(self.image.width(), self.image.height()) > 256:
            image = image.scaled(QSize(256, 256), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap = QPixmap.fromImage(image)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec_(Qt.CopyAction)


