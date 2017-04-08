# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2016 by Wilbert Berendsen
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
A page that can display a SVG document.

"""

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PyQt5.QtGui import QColor,QImage, QPainter
from PyQt5.QtSvg import QSvgRenderer

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)

from . import page
from . import render


class BasicSvgPage(page.AbstractPage):
    """A page that can display a SVG document."""
    def __init__(self, load_file=None):
        self._svg_r = QSvgRenderer()
        if load_file:
            self.load(load_file)

    def load(self, load_file):
        """Load filename or QByteArray."""
        success = self._svg_r.load(load_file)
        if success:
            self.pageWidth = self._svg_r.defaultSize().width()
            self.pageHeight = self._svg_r.defaultSize().height()
        return success

    def paint(self, painter, rect, callback=None):
        painter.fillRect(rect, self.paperColor or QColor(Qt.white))
        page = QRect(0, 0, self.width, self.height)
        painter.translate(page.center())
        painter.rotate(self.computedRotation * 90)
        if self.computedRotation & 1:
            page.setSize(page.size().transposed())
        painter.translate(-page.center())
        self._svg_r.render(painter, QRectF(page))


class SvgPage(BasicSvgPage):
    """Display SVG pages using a cache."""
    def __init__(self, load_file=None, renderer=None):
        super().__init__(load_file)
        if renderer is not None:
            self.renderer = renderer

    def paint(self, painter, rect, callback=None):
        self.renderer.paint(self, painter, rect, callback)


class Renderer(render.AbstractImageRenderer):
    """Render SVG pages.

    Additional instance attributes:

        imageFormat     (QImage.Format_ARGB32_Premultiplied) the QImage format to use.

    """
    # QImage format to use
    imageFormat = QImage.Format_ARGB32_Premultiplied

    def render(self, page):
        """Generate an image for this Page."""
        i = QImage(page.width, page.height, self.imageFormat)
        i.fill(page.paperColor or self.paperColor or QColor(Qt.white))
        painter = QPainter(i)
        rect = QRect(0, 0, page.width, page.height)
        painter.translate(rect.center())
        painter.rotate(page.computedRotation * 90)
        if page.computedRotation & 1:
            rect.setSize(rect.size().transposed())
        painter.translate(-rect.center())
        page._svg_r.render(painter, QRectF(rect))
        return i


# install a default renderer, so PopplerPage can be used directly
SvgPage.renderer = Renderer()




