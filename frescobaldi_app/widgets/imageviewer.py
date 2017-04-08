# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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


from PyQt5.QtCore import pyqtSignal, QMimeData, QSize, QRect, Qt
from PyQt5.QtGui import QColor, QDrag, QImage, QPainter, QPalette, QPixmap
from PyQt5.QtWidgets import QApplication, QScrollArea, QSizePolicy, QWidget


__all__ = ['ImageViewer']


# internal constants
MOVE = 1
DRAG = 2


class ImageViewer(QScrollArea):

    actualSizeChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent, alignment=Qt.AlignCenter)
        self._actualsize = True
        self._image = QImage()
        self.setBackgroundRole(QPalette.Dark)
        self.setWidget(ImageWidget(self))

    def setActualSize(self, enabled=True):
        if enabled == self._actualsize:
            return
        self.setWidgetResizable(not enabled)
        if enabled and not self._image.isNull():
            self.widget().resize(self._image.size())
        self._actualsize = enabled
        self.actualSizeChanged.emit(enabled)

    def actualSize(self):
        return self._actualsize

    def setImage(self, image):
        self._image = image
        self._pixmap = None
        self._pixmapsize = None
        if self._actualsize:
            self.widget().resize(image.size())
        self.widget().update()

    def image(self):
        return self._image

    def pixmap(self, size):
        """Returns (and caches) a scaled pixmap for the image."""
        if self._pixmapsize == size:
            return self._pixmap
        self._pixmap = QPixmap.fromImage(
            self._image.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self._pixmapsize = size
        return self._pixmap

    def startDrag(self):
        image = self.image()
        data = QMimeData()
        data.setImageData(image)
        drag = QDrag(self)
        drag.setMimeData(data)
        if max(image.width(), image.height()) > 256:
            image = image.scaled(QSize(256, 256), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p = QPainter()
        p.begin(image)
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p.fillRect(image.rect(), QColor(0, 0, 0, 160))
        p.end()
        pixmap = QPixmap.fromImage(image)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec_(Qt.CopyAction)


class ImageWidget(QWidget):
    def __init__(self, viewer):
        super(ImageWidget, self).__init__()
        self.viewer = viewer
        self.setBackgroundRole(QPalette.Dark)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._mode = None
        self._startpos = None

    def paintEvent(self, ev):
        image = self.viewer.image()
        painter = QPainter(self)
        if self.size() == image.size():
            painter.drawImage(ev.rect(), image, ev.rect())
        else:
            s = image.size()
            s.scale(self.size(), Qt.KeepAspectRatio)
            r = QRect()
            r.setSize(s)
            r.moveCenter(self.rect().center())
            painter.drawPixmap(r, self.viewer.pixmap(s))

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
            self.viewer.startDrag()

    def mouseReleaseEvent(self, ev):
        mode, self._mode = self._mode, None
        if (ev.button() == Qt.LeftButton and
                mode == DRAG and ev.globalPos() == self._startpos):
            self.viewer.setActualSize(not self.viewer.actualSize())


