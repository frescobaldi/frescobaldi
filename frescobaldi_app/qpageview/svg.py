# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
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
    """A page that can display a SVG document.
    
    This class just paints the image every time it is requested, without
    caching it, which is too slow for normal use. Use SvgPage instead.
    
    """
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
            self._viewBox = self._svg_r.viewBoxF()
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
    
    def mutex(self):
        return self._svg_r


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

    def render(self, page, key, tile):
        """Generate an image for the tile of this Page."""
        i = QImage(tile.w, tile.h, self.imageFormat)
        i.fill(page.paperColor or self.paperColor or QColor(Qt.white))
        painter = QPainter(i)
        
        # rotate the painter accordingly
        rect = QRect(0, 0, tile.w, tile.h)
        painter.translate(rect.center())
        painter.rotate(key.rotation * 90)
        if key.rotation & 1:
            rect.setSize(rect.size().transposed())
        painter.translate(-rect.center())
        
        # now determine the part to draw
        
        # convert tile to viewbox
        b = page._viewBox
        
        if key.rotation == 0:
            hscale = key.width / b.width()
            vscale = key.height / b.height()
            x = tile.x / hscale + b.x()
            y = tile.y / vscale + b.y()
        elif key.rotation == 1:
            hscale = key.height / b.width()
            vscale = key.width / b.height()
            x = tile.y / hscale + b.x()
            y = (key.width - tile.w - tile.x) / vscale + b.y()
        elif key.rotation == 2:
            hscale = key.width / b.width()
            vscale = key.height / b.height()
            x = (key.width - tile.w - tile.x) / hscale + b.x()
            y = (key.height - tile.h - tile.y) / vscale + b.y()
        else: # key.rotation == 3:
            hscale = key.height / b.width()
            vscale = key.width / b.height()
            x = (key.height - tile.h - tile.y) / vscale + b.x()
            y = tile.x / hscale + b.y()
        # why does this work? I'd assume w and h need to be swapped 
        # for rotation 1 and 3, but that yields strange misdrawings...
        w = tile.w / hscale
        h = tile.h / vscale
            
        page._svg_r.setViewBox(QRectF(x, y, w, h))
        page._svg_r.render(painter)
        page._svg_r.setViewBox(page._viewBox)
        return i


# install a default renderer, so PopplerPage can be used directly
SvgPage.renderer = Renderer()




