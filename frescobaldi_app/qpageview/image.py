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


from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QImage, QPainter, QTransform

from . import page
from . import util


class ImagePage(page.AbstractPage):
    dpi = 96   # TODO: maybe this can be image dependent.
    imageFormat = QImage.Format_ARGB32_Premultiplied
    
    def __init__(self, image):
        super().__init__()
        self._image = image
        self.setPageSize(image.size())
    
    def paint(self, painter, rect, callback=None):
        """Paint our image in the View."""
        source = self.mapFromPage().rect(rect)
        painter.setTransform(self.transform(), True)
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

        source = self.mapFromPage().rect(rect)
        target = m.mapRect(source).toRect()
        image = QImage(target.size(), self.imageFormat)
        painter = QPainter(image)
        painter.translate(-target.topLeft())
        painter.setTransform(m, True)
        painter.drawImage(source, self._image, source)
        return image

