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
Interface with popplerqt5, popplerqt5-specific classes etc.

Only this module depends on popplerqt5.

"""

from PyQt5.QtCore import Qt

import popplerqt5

from . import page
from . import locking
from . import render

from .constants import (
    Rotate_0,
)


class PopplerPage(page.AbstractPage):
    """A Page capable of displaying one page of a Poppler.Document instance.

    It has two additional instance attributes:

        `document`: the Poppler.Document instance
        `pageNumber`: the page number to render

    """
    def __init__(self, document, pageNumber, renderer=None):
        super().__init__()
        self.document = document
        self.pageNumber = pageNumber
        self.setPageSize(document.page(pageNumber).pageSizeF())
        if renderer is not None:
            self.renderer = renderer

    @classmethod
    def createPages(cls, document, renderer=None):
        """Convenience class method returning a list of instances of this class.

        The Page instances are created from the document, in page number order.
        The specified Renderer is used, or else the global poppler renderer.

        """
        return [cls(document, num, renderer) for num in range(document.numPages())]

    def mutex(self):
        """No two pages of same Poppler document are rendered at the same time."""
        return self.document


class Renderer(render.AbstractImageRenderer):
    renderHint = (
        popplerqt5.Poppler.Document.Antialiasing |
        popplerqt5.Poppler.Document.TextAntialiasing
    )
    renderBackend = popplerqt5.Poppler.Document.SplashBackend
    oversampleThreshold = 96

    def key(self, page):
        """Reimplemented to keep a reference to the poppler document."""
        key = super().key(page)
        return render.cache_key(
            page.document,
            (page.pageNumber, page.computedRotation),
            key.size)

    def render(self, page):
        """Generate an image for this Page."""
        doc = page.document
        num = page.pageNumber
        p = doc.page(num)
        s = page.pageSize()
        if page.computedRotation & 1:
            s.transpose()

        xres = 72.0 * page.width / s.width()
        yres = 72.0 * page.height / s.height()
        multiplier = 2 if xres < self.oversampleThreshold else 1
        image = self.render_poppler_image(doc, num,
            xres * multiplier, yres * multiplier,
            0, 0, page.width * multiplier, page.height * multiplier,
            page.computedRotation, page.paperColor or self.paperColor)
        if multiplier == 2:
            image = image.scaledToWidth(page.width, Qt.SmoothTransformation)
        image.setDotsPerMeterX(xres * 39.37)
        image.setDotsPerMeterY(yres * 39.37)
        return image

    def render_poppler_image(self, doc, pageNum,
                                   xres=72.0, yres=72.0,
                                   x=-1, y=-1, w=-1, h=-1, rotate=Rotate_0,
                                   paperColor=None):
        """Render an image, almost like calling page.renderToImage().

        The document is properly locked during rendering and render options
        are set.

        """
        with locking.lock(doc):
            if self.renderHint is not None:
                doc.setRenderHint(int(doc.renderHints()), False)
                doc.setRenderHint(self.renderHint)
            if paperColor is not None:
                doc.setPaperColor(paperColor)
            if self.renderBackend is not None:
                doc.setRenderBackend(self.renderBackend)
            image = doc.page(pageNum).renderToImage(xres, yres, x, y, w, h, rotate)
        image.setDotsPerMeterX(xres * 39.37)
        image.setDotsPerMeterY(yres * 39.37)
        return image



# install a default renderer, so PopplerPage can be used directly
PopplerPage.renderer = Renderer()



