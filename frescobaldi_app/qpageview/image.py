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
A page that can display an image, loaded using QImage.

ImagePages are instantiated quite fast. The image is only really loaded on first
display.

"""

from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QImageReader, QPainter, QTransform

from . import locking
from . import page
from . import render


class ImageContainer:
    """Represent an image, is shared among copies of the "same" Page."""
    def __init__(self, source, autoTransform):
        self.source = source
        self.autoTransform = autoTransform

    def image(self, clip=None):
        """Load and return the image.

        If clip is given, it should be a QRect describing the area to load.

        """
        with locking.lock(self):
            reader = QImageReader(self.source)
            reader.setAutoTransform(self.autoTransform)
            if clip:
                # TODO: really only load the clip, obeying the transformation...
                return reader.read().copy(clip)
            return reader.read()


class ImagePage(page.AbstractRenderedPage):
    """A Page that displays an image in any file format supported by Qt."""
    autoTransform = True    # whether to automatically apply exif transformations
    dpi = 96   # TODO: maybe this can be image dependent.
    
    def __init__(self, filename, size, renderer=None):
        super().__init__(renderer)
        self.setPageSize(size)
        self._ic = ImageContainer(filename, self.autoTransform)

    @classmethod
    def load(cls, filename, renderer=None):
        """Load the image and yield one ImagePage instance if loading was successful."""
        reader = QImageReader(filename)
        reader.setAutoTransform(cls.autoTransform)
        if reader.canRead():
            size = reader.size()
            if size:
                if cls.autoTransform and reader.transformation() & 4:
                    size.transpose()
                yield cls(filename, size, renderer)

    def print(self, painter, rect=None, paperColor=None):
        """Paint a page for printing."""
        if rect is None:
            image = self._ic.image()
        else:
            rect = rect.normalized() & self.pageRect()
            # we copy the image, because QSvgGenerator otherwise includes the
            # full image in the resulting SVG file!
            image = self._ic.image(rect.toRect())
        painter.drawImage(QPoint(0, 0), image)

    def image(self, rect=None, dpiX=None, dpiY=None, paperColor=None):
        """Return a QImage of the specified rectangle."""
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
        return self._ic._image(source).transformed(m, Qt.SmoothTransformation)

    def group(self):
        return self._ic
    
    def mutex(self):
        return self._ic


class ImageRenderer(render.AbstractRenderer):
    def draw(self, page, painter, key, tile, paperColor=None):
        """Draw the specified tile of the page (coordinates in key) on painter."""
        # determine the part to draw; convert tile to viewbox
        source = self.map(key, page.pageRect()).mapRect(QRect(*tile))
        target = QRect(0, 0, tile.w, tile.h)
        if key.rotation & 1:
            target.setSize(target.size().transposed())
        image = page._ic.image(source).scaled(
            target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawImage(target, image)



# install a default renderer, so SvgPage can be used directly
ImagePage.renderer = ImageRenderer()

