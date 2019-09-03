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
    
    def __init__(self, svgrenderer, renderer=None):
        super().__init__()
        self._svg = svgrenderer
        self.pageWidth = svgrenderer.defaultSize().width()
        self.pageHeight = svgrenderer.defaultSize().height()
        self._viewBox = svgrenderer.viewBoxF()
        if renderer is not None:
            self.renderer = renderer

    @classmethod
    def load(cls, filename, renderer=None):
        """Load a SVG document from filename, which may also be a QByteArray."""
        r = QSvgRenderer()
        if r.load(filename):
            return cls(r, renderer)

    @classmethod
    def loadFiles(cls, filenames, renderer=None):
        """Yield a SvgPage for every file that successfully loads.

        filenames is an iterable of files, a filename may also be a QByteArray.

        """
        for f in filenames:
            p = cls.load(f, renderer)
            if p:
                yield p

    def mutex(self):
        return self._svg


class Renderer(render.AbstractImageRenderer):
    """Render SVG pages."""
    def draw(self, page, painter, key, tile, paperColor):
        """Draw the specified tile of the page (coordinates in key) on painter."""
        # determine the part to draw; convert tile to viewbox
        viewbox = self.map(key, page._viewBox).mapRect(QRectF(*tile))
        target = QRectF(0, 0, tile.w, tile.h)
        if key.rotation & 1:
            target.setSize(target.size().transposed())
        with locking.lock(page._svg):
            page._svg.setViewBox(viewbox)
            # we must specify the target otherwise QSvgRenderer scales to the
            # unrotated image
            page._svg.render(painter, target)
            page._svg.setViewBox(page._viewBox)




# install a default renderer, so SvgPage can be used directly
SvgPage.renderer = Renderer()




