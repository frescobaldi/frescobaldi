# -*- coding: utf-8 -*-
#
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
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtSvg import QSvgRenderer

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)

from . import document
from . import locking
from . import page
from . import render


class SvgPage(page.AbstractRenderedPage):
    """A page that can display a SVG document."""

    dpi = 90.0

    def __init__(self, svgrenderer, renderer=None):
        super().__init__(renderer)
        self._svg = svgrenderer
        self.pageWidth = svgrenderer.defaultSize().width()
        self.pageHeight = svgrenderer.defaultSize().height()
        self._viewBox = svgrenderer.viewBoxF()

    @classmethod
    def load(cls, filename, renderer=None):
        """Load a SVG document from filename, which may also be a QByteArray.

        Yields only one Page instance, as SVG currently supports one page per
        file. If the file can't be loaded by the underlying QSvgRenderer,
        no Page is yielded.

        """
        r = QSvgRenderer()
        if r.load(filename):
            yield cls(r, renderer)

    def mutex(self):
        return self._svg

    def group(self):
        return self._svg


class SvgDocument(document.MultiSourceDocument):
    """A Document representing a group of SVG files."""
    pageClass = SvgPage

    def createPages(self):
        return self.pageClass.loadFiles(self.sources(), self.renderer)


class SvgRenderer(render.AbstractRenderer):
    """Render SVG pages."""
    def setRenderHints(self, painter):
        """Sets the renderhints for the painter we want to use."""
        painter.setRenderHint(QPainter.Antialiasing, self.antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing, self.antialiasing)

    def draw(self, page, painter, key, tile, paperColor=None):
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
            painter.save()
            painter.setClipRect(target, Qt.IntersectClip)
            # QSvgRenderer seems to set antialiasing always on anyway... :-)
            self.setRenderHints(painter)
            page._svg.render(painter, target)
            painter.restore()
            page._svg.setViewBox(page._viewBox)




# install a default renderer, so SvgPage can be used directly
SvgPage.renderer = SvgRenderer()




