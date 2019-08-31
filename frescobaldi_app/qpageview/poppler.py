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
Interface with popplerqt5, popplerqt5-specific classes etc.

Only this module depends on popplerqt5.

You need this module to display PDF documents.

"""

import weakref

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPicture, QTransform

import popplerqt5

from . import page
from . import link
from . import locking
from . import render

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)



# store the links in the page of a Poppler document as long as the document exists
_linkscache = weakref.WeakKeyDictionary()


class Link(link.Link):
    """A Link that encapsulates a Poppler.Link object."""
    def __init__(self, linkobj):
        self.linkobj = linkobj
        self.area = link.Area(*linkobj.linkArea().normalized().getCoords())
    
    @property
    def url(self):
        if isinstance(self.linkobj, popplerqt5.Poppler.LinkBrowse):
            return self.linkobj.url()
        return ""


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

    @classmethod
    def loadDocument(cls, filename, renderer=None):
        """Load a Poppler document, and return a list of instances of this class.

        The filename can also be a QByteArray.
        The specified Renderer is used, or else the global poppler renderer.

        """
        doc = popplerqt5.Poppler.Document.load(filename)
        return cls.createPages(doc, renderer)

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
        rect = self.mapFromPage(self.pageWidth, self.pageHeight).rect(rect)
        with locking.lock(self.document):
            page = self.document.page(self.pageNumber)
            return page.text(rect)
    
    def links(self):
        """Reimplemented to use a different caching mechanism."""
        document, pageNumber = self.document, self.pageNumber
        try:
            return _linkscache[document][pageNumber]
        except KeyError:
            with locking.lock(document):
                links = link.Links(map(Link, document.page(pageNumber).links()))
            _linkscache.setdefault(document, {})[pageNumber] = links
            return links


class Renderer(render.AbstractImageRenderer):
    renderHint = (
        popplerqt5.Poppler.Document.Antialiasing |
        popplerqt5.Poppler.Document.TextAntialiasing
    )
    renderBackend = popplerqt5.Poppler.Document.SplashBackend
    printRenderBackend = popplerqt5.Poppler.Document.SplashBackend

    oversampleThreshold = 96
    printResolution = 300   # (only for SplashBackend)
    
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
            if paperColor:
                oldcolor = doc.paperColor()
                doc.setPaperColor(paperColor)
            if self.renderBackend is not None:
                doc.setRenderBackend(self.renderBackend)
                oldbackend = doc.renderBackend()
            image = doc.page(pageNum).renderToImage(xres, yres, x, y, w, h, rotate)
            if paperColor:
                doc.setPaperColor(oldcolor)
            if self.renderBackend is not None:
                doc.setRenderBackend(oldbackend)
        return image

    def draw(self, page, painter, key, tile):
        """Draw a tile on the painter.

        The painter is already at the right position and rotation.
        For the Poppler page and renderer, draw() is only used for printing.
        (See AbstractPage.print().)

        """
        source = self.map(key, page.pageRect()).mapRect(QRectF(*tile))
        target = QRectF(0, 0, tile.w, tile.h)
        if key.rotation & 1:
            target.setSize(target.size().transposed())

        doc = page.document
        p = doc.page(page.pageNumber)
        paperColor = page.paperColor or self.paperColor

        with locking.lock(doc):
            if self.renderHint is not None:
                doc.setRenderHint(int(doc.renderHints()), False)
                doc.setRenderHint(self.renderHint)
            if paperColor:
                oldcolor = doc.paperColor()
                doc.setPaperColor(paperColor)
            if self.printRenderBackend is not None:
                doc.setRenderBackend(self.printRenderBackend)
                oldbackend = doc.renderBackend()
            if self.printRenderBackend == popplerqt5.Poppler.Document.ArthurBackend:
                # Poppler's Arthur backend removes the current transform from
                # the painter (it sets a default CTM, instead of combining it
                # with the current transform. We let Poppler draw on a QPicture,
                # and draw that on our painter.
                q = QPicture()
                p.renderToPainter(QPainter(q), page.dpi, page.dpi, source.x(), source.y(), source.width(), source.height())
                q.play(painter)
            else:
                # map to printer resolution
                dpiX = painter.device().logicalDpiX()
                dpiY = painter.device().logicalDpiY()
                # TODO account for extra (down)scaling...
                s = QTransform().scale(dpiX / page.dpi, dpiY / page.dpi).mapRect(source)
                img = p.renderToImage(dpiX, dpiY, s.x(), s.y(), s.width(), s.height())
                painter.drawImage(target, img, QRectF(img.rect()))
            if paperColor:
                doc.setPaperColor(oldcolor)
            if self.printRenderBackend is not None:
                doc.setRenderBackend(oldbackend)



# install a default renderer, so PopplerPage can be used directly
PopplerPage.renderer = Renderer()



