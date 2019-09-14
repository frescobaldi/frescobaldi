# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
A page that can display a QImage,
without using a renderer.

ImagePages are instantiated quite fast. The image is only really loaded on first
display.

"""


from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QImage, QImageReader, QPainter, QTransform

from . import page
from . import util


class ImagePage(page.AbstractPage):
    """A Page that displays an image in any file format supported by Qt."""
    autoTransform = True    # whether to automatically apply exif transformations
    dpi = 96   # TODO: maybe this can be image dependent.
    downScaledSize = 200
    
    def __init__(self, filename, size, image=None):
        super().__init__()
        self.source = filename
        self.setPageSize(size)
        self._image = image
        self._imageJob = None
        self._imageDownScaled = None

    @classmethod
    def load(cls, filename, renderer=None):
        """Load the image and yield one ImagePage instance if loading was successful.

        The renderer argument is not used.

        """
        reader = QImageReader(filename)
        reader.setAutoTransform(cls.autoTransform)
        if reader.canRead():
            image = None
            size = reader.size()
            if size:
                if cls.autoTransform and reader.transformation() & 4:
                    size.transpose()
            else:
                # in the unlikely case the size can't be determined, read the image
                image = reader.read()
                if image.isNull():
                    size = QSize(100, 100)  # prevent layout error etc
                else:
                    size = image.size()
            yield cls(filename, size, image)

    def _loadImage(self):
        """Internal. Construct an image reader and return the image."""
        reader = QImageReader(self.source)
        reader.setAutoTransform(self.autoTransform)
        return reader.read()

    def _materialize(self):
        """Internal. If needed, load the image and deletes the image reader."""
        if self._image is None:
            self._image = self._loadImage()

    def _materializeInBackground(self, callback):
        """Internal. Load the image in the background without blocking the main thread."""
        job = self._imageJob
        if job is None:
            from . import backgroundjob
            job = self._imageJob = backgroundjob.Job()
            job.work = self._loadImage
            job.callbacks = callbacks = set()
            def finalize(result):
                self._image = result
                self._imageJob = None
                self._imageDownScaled = None
                for cb in callbacks:
                    callback(self)
            job.finalize = finalize
            job.start()
        if callback:
            job.callbacks.add(callback)

    def _downScale(self):
        """Scales the image down to save memory."""
        w, h = self._image.width(), self._image.height()
        if max(w, h) > self.downScaledSize:
            self._imageDownScaled = self._image.scaled(
                QSize(self.downScaledSize, self.downScaledSize),
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._image = None
            
    def paint(self, painter, rect, callback=None):
        """Paint our image in the View."""
        if self._image is None:
            self._materializeInBackground(callback)
            if self._imageDownScaled:
                image = self._imageDownScaled
            else:
                # temporary background color
                painter.fillRect(rect, self.paperColor or Qt.white)
                return
        elif self._image.isNull():
            # image couldn't be loaded
            painter.fillRect(rect, self.paperColor or Qt.white)
            # TODO: paint some icon indicating load failure
            return
        else:
            image = self._image
        w, h = image.width(), image.height()
        source = self.mapFromPage(w, h).rect(rect)
        painter.setTransform(self.transform(w, h), True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawImage(source, image, source)

    def print(self, painter, rect=None, paperColor=None):
        """Paint a page for printing."""
        self._materialize()
        if rect is None:
            image = self._image
        else:
            rect = rect.normalized() & self.pageRect()
            # we copy the image, because QSvgGenerator otherwise includes the
            # full image in the resulting SVG file!
            image = self._image.copy(rect.toRect())
        painter.drawImage(QPoint(0, 0), image)

    def image(self, rect=None, dpiX=None, dpiY=None, paperColor=None):
        """Return a QImage of the specified rectangle."""
        self._materialize()
        if rect is None:
            rect = self.rect()
        else:
            rect = rect & self.rect()
        if dpiX is None:
            dpiX = self.dpi
        if dpiY is None:
            dpiY = dpiX

        s = self.defaultSize()
        m = QTransform()
        m.scale(s.width() * dpiX / self.dpi, s.height() * dpiY / self.dpi)
        m.translate(.5, .5)
        m.rotate(self.computedRotation * 90)
        m.translate(-.5, -.5)
        m.scale(1 / self.pageWidth, 1 / self.pageHeight)

        source = self.transform().inverted()[0].mapRect(rect)
        return self._image.copy(source).transformed(m, Qt.SmoothTransformation)

