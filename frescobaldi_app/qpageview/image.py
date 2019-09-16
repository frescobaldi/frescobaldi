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

import time
import weakref

from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QImage, QImageReader, QPainter, QTransform

from .locking import lock
from . import page
from . import util
from . import multipage


_pool = weakref.WeakSet()
_currentsize = 0
_cleanupjob = None
maxsize = 209715200



class ImageContainer:
    """Represent an image, is shared among copies of the "same" Page."""
    def __init__(self, source, image, autoTransform):
        self._source = source
        self._image = image
        self._autoTransform = autoTransform
        self._imageJob = None
        self._thumbnail = None
        self._thumbnailJob = None
        self._time = 0
        if image is not None:
            manage(self)
        
    def _loadImage(self):
        """Internal. Construct an image reader and return the image."""
        with lock(self):
            reader = QImageReader(self._source)
            reader.setAutoTransform(self._autoTransform)
            return reader.read()

    def _materialize(self):
        """Internal. If needed, load the image and deletes the image reader."""
        if self._image is None:
            self._image = self._loadImage()
    
    def _materializeInBackground(self, page, callback):
        job = self._imageJob
        if job is None:
            from . import backgroundjob
            job = self._imageJob = backgroundjob.Job()
            job.work = self._loadImage
            job.callbacks = callbacks = set()
            def finalize(result):
                self._image = result
                self._imageJob = None
                for cb in callbacks:
                    callback(None)
                manage(self)
            job.finalize = finalize
            job.start()
        if callback:
            callback = multipage.CallBack(callback, page)
            job.callbacks.add(callback)
    
    def _createThumbnail(self):
        return self._image.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _thumbnailInBackground(self):
        job = self._thumbnailJob
        if job is None:
            from . import backgroundjob            
            job = self._thumbnailJob = backgroundjob.Job()
            job.work = self._createThumbnail
            def finalize(result):
                self._thumbnail = result
                self._thumbnailJob = None
                self._image = None
            job.finalize = finalize
            job.start()

    def image(self):
        """Return the image if present."""
        self._time = time.time()
        return self._image or self._thumbnail


class ImagePage(page.AbstractPage):
    """A Page that displays an image in any file format supported by Qt."""
    autoTransform = True    # whether to automatically apply exif transformations
    dpi = 96   # TODO: maybe this can be image dependent.
    
    def __init__(self, filename, size, image=None):
        super().__init__()
        self._ic = ImageContainer(filename, image, self.autoTransform)
        self.setPageSize(size)

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

    def paint(self, painter, rect, callback=None):
        """Paint our image in the View."""
        image = self._ic.image()
        if image is not None:
            if image.isNull():
                # image couldn't be loaded
                painter.fillRect(rect, self.paperColor or Qt.white)
                # TODO: paint some icon indicating load failure
                return
            elif image.width() < (self.height if self.computedRotation & 1 else self.width):
                self._ic._materializeInBackground(self, callback)
        else:
            self._ic._materializeInBackground(self, callback)
            painter.fillRect(rect, self.paperColor or Qt.white)
            return
        w, h = image.width(), image.height()
        source = self.mapFromPage(w, h).rect(rect)
        painter.setTransform(self.transform(w, h), True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawImage(source, image, source)

    def print(self, painter, rect=None, paperColor=None):
        """Paint a page for printing."""
        self._ic._materialize()
        image = self._ic.image()
        if rect is not None:
            rect = rect.normalized() & self.pageRect()
            # we copy the image, because QSvgGenerator otherwise includes the
            # full image in the resulting SVG file!
            image = image.copy(rect.toRect())
        painter.drawImage(QPoint(0, 0), image)

    def image(self, rect=None, dpiX=None, dpiY=None, paperColor=None):
        """Return a QImage of the specified rectangle."""
        self._ic._materialize()
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
        return self._ic._image.copy(source).transformed(m, Qt.SmoothTransformation)


def manage(ic):
    """Keep track of memory usage of all pages."""
    global _cleanupjob, _pool, _currentsize, maxsize
    _pool.add(ic)
    _currentsize += ic._image.byteCount()
    if _currentsize < maxsize:
        return
    _currentsize = 0
    
    # newest first
    ics = iter(sorted(_pool, key = lambda ic: ic._time, reverse=True))
    for ic in ics:
        _currentsize += ic._image.byteCount()
        if _currentsize > maxsize:
            break
    ics = list(ics)
    _pool.difference_update(ics)
    for ic in ics:
        ic._thumbnailInBackground()


