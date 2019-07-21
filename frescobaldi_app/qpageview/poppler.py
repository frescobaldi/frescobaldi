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

import weakref

from PyQt5.QtCore import Qt, QRectF

import popplerqt5

from . import page
from . import locking
from . import render
from . import rectangles

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)



# store the links in the page of a Poppler document as long as the document exists
_linkscache = weakref.WeakKeyDictionary()


def get_links(page):
    """Return a Links object.
    
    The returned object is a position-searchable list of the links in a page.
    See the rectangles documentation.
    
    """
    document, pageNumber = page.document, page.pageNumber
    try:
        return _linkscache[document][pageNumber]
    except KeyError:
        with locking.lock(document):
            links = Links(document.page(pageNumber).links())
        _linkscache.setdefault(document, {})[pageNumber] = links
        return links


class Links(rectangles.Rectangles):
    """Represents a position searchable list of links in a poppler PDF page."""
    def get_coords(self, obj):
        return obj.linkArea().normalized().getCoords()


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
    
    def group(self):
        """Reimplemented to return the Poppler document our page displays a page from."""
        return self.document
    
    def ident(self):
        """Reimplemented to return the page number of this page."""
        return self.pageNumber

    def text(self, rect):
        """Returns text inside rectangle."""
        rect = self.page2area(rect, self.pageWidth, self.pageHeight)
        with locking.lock(self.document):
            page = self.document.page(self.pageNumber)
            return page.text(rect)

    def linksAt(self, point):
        """Return a list() of zero or more links touched by QPoint point.

        The point is in page coordinates.
        The list is sorted with the smallest rectangle first.

        """
        # Poppler.Link objects have their linkArea() ranging
        # in width and height from 0.0 to 1.0 ...
        x, y = self.point2area(point.x(), point.y(), 1, 1)
        links = get_links(self)
        return sorted(links.at(x, y), key=links.width)

    def linksIn(self, rect):
        """Return an unordered set of links enclosed in rectangle.
        
        The rectangle is in page coordinates.
        
        """
        return get_links(self).inside(*self.page2area(rect, 1, 1).getCoords())

    def linkRect(self, link):
        """Return a QRect encompassing the linkArea of a link in coordinates of our page."""
        return self.area2page(link.linkArea(), 1, 1)


class Renderer(render.AbstractImageRenderer):
    renderHint = (
        popplerqt5.Poppler.Document.Antialiasing |
        popplerqt5.Poppler.Document.TextAntialiasing
    )
    renderBackend = popplerqt5.Poppler.Document.SplashBackend
    oversampleThreshold = 96

    def render(self, page, key, tile):
        """Generate an image for the Page referred to by key."""
        doc = page.document
        num = page.pageNumber
        s = page.pageSize()
        if key.rotation & 1:
            s.transpose()

        xres = 72.0 * key.width / s.width()
        yres = 72.0 * key.height / s.height()
        multiplier = 2 if xres < self.oversampleThreshold else 1
        image = self.render_poppler_image(doc, num,
            xres * multiplier, yres * multiplier,
            tile.x * multiplier, tile.y * multiplier, tile.w * multiplier, tile.h * multiplier,
            key.rotation, page.paperColor or self.paperColor)
        if multiplier == 2:
            image = image.scaledToWidth(tile.w, Qt.SmoothTransformation)
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
        return image



# install a default renderer, so PopplerPage can be used directly
PopplerPage.renderer = Renderer()



