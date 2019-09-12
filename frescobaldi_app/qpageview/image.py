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

"""


from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QImage, QPainter, QTransform

from . import page
from . import util


class ImagePage(page.AbstractPage):
    dpi = 96   # TODO: maybe this can be image dependent.
    
    def __init__(self, image):
        super().__init__()
        self._image = image
        self.setPageSize(image.size())
    
    @classmethod
    def load(cls, filename, renderer=None):
        """Load the image and yield one ImagePage instance if loading was successful.

        The renderer argument is not used.

        """
        if isinstance(filename, str):
            image = QImage(filename)
        else:
            image = QImage.fromData(filename)
        if not image.isNull():
            yield cls(image)

    def paint(self, painter, rect, callback=None):
        """Paint our image in the View."""
        source = self.mapFromPage().rect(rect)
        painter.setTransform(self.transform(), True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawImage(source, self._image, source)

    def print(self, painter, rect=None, paperColor=None):
        """Paint a page for printing."""
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

