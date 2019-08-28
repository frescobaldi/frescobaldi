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

from PyQt5.QtCore import QRect, QRectF, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtSvg import QSvgRenderer

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)

from . import locking
from . import page
from . import render


class SvgPage(page.AbstractPage):
    """A page that can display a SVG document."""

    dpi = 90.0
    
    def __init__(self, load_file=None, renderer=None):
        super().__init__()
        self._svg_r = QSvgRenderer()
        if renderer is not None:
            self.renderer = renderer
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

    def mutex(self):
        return self._svg_r


class Renderer(render.AbstractImageRenderer):
    """Render SVG pages."""
    def draw(self, painter, page, key, tile):
        """Draw the specified tile of the page (coordinates in key) on painter."""
        # determine the part to draw; convert tile to viewbox
        viewbox = self.map(key, page._viewBox).mapRect(QRectF(*tile))
        target = QRectF(0, 0, tile.w, tile.h)
        if key.rotation & 1:
            target.setSize(target.size().transposed())
        with locking.lock(page._svg_r):
            page._svg_r.setViewBox(viewbox)
            # we must specify the target otherwise QSvgRenderer scales to the
            # unrotated image
            page._svg_r.render(painter, target)
            page._svg_r.setViewBox(page._viewBox)

    def print(self, page, painter, rect):
        """Paints the desired part of the page to the painter for printing."""
        ### compute viewbox, rect corresponds to the original size
        hscale = page._viewBox.width() / page.pageWidth
        vscale = page._viewBox.height() / page.pageHeight
        x = page._viewBox.x() + rect.x() * hscale
        y = page._viewBox.y() + rect.y() * vscale
        w = rect.width() * hscale
        h = rect.height() * vscale
        with locking.lock(page._svg_r):
            page._svg_r.setViewBox(QRectF(x, y, w, h))
            page._svg_r.render(painter)
            page._svg_r.setViewBox(page._viewBox)



# install a default renderer, so SvgPage can be used directly
SvgPage.renderer = Renderer()




