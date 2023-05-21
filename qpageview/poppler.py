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
Interface with popplerqt5, popplerqt5-specific classes etc.

This module depends on popplerqt5, although it can be imported when
popplerqt5 is not available.

You need this module to display PDF documents.

"""

import contextlib
import weakref

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QRegion, QPainter, QPicture, QTransform

try:
    import popplerqt5
except ImportError:
    popplerqt5 = None

from . import document
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
        """The url the link points to."""
        if isinstance(self.linkobj, popplerqt5.Poppler.LinkBrowse):
            return self.linkobj.url()
        return ""


class PopplerPage(page.AbstractRenderedPage):
    """A Page capable of displaying one page of a Poppler.Document instance.

    It has two additional instance attributes:

        `document`: the Poppler.Document instance
        `pageNumber`: the page number to render

    """
    def __init__(self, document, pageNumber, renderer=None):
        super().__init__(renderer)
        self.document = document
        self.pageNumber = pageNumber
        self.setPageSize(document.page(pageNumber).pageSizeF())

    @classmethod
    def loadPopplerDocument(cls, document, renderer=None, pageSlice=None):
        """Convenience class method yielding instances of this class.

        The Page instances are created from the document, in page number order.
        The specified Renderer is used, or else the global poppler renderer.
        If pageSlice is given, it should be a slice object and only those pages
        are then loaded.

        """
        it = range(document.numPages())
        if pageSlice is not None:
            it = it[pageSlice]
        for num in it:
            yield cls(document, num, renderer)

    @classmethod
    def load(cls, filename, renderer=None):
        """Load a Poppler document, and yield of instances of this class.

        The filename can also be a QByteArray or a popplerqt5.Poppler.Document
        instance. The specified Renderer is used, or else the global poppler
        renderer.

        """
        doc = load(filename)
        return cls.loadPopplerDocument(doc, renderer) if doc else ()

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


class PopplerDocument(document.SingleSourceDocument):
    """A lazily loaded Poppler (PDF) document."""
    pageClass = PopplerPage

    def __init__(self, source=None, renderer=None):
        super().__init__(source, renderer)
        self._document = None

    def invalidate(self):
        """Reimplemented to clear the Poppler Document reference."""
        super().invalidate()
        self._document = None

    def createPages(self):
        doc = self.document()
        if doc:
            return self.pageClass.loadPopplerDocument(doc, self.renderer)
        return ()

    def document(self):
        """Return the Poppler Document object.

        Returns None if no source was yet set, and False if loading failed.

        """
        if self._document is None:
            source = self.source()
            if source:
                self._document = load(source) or False
        return self._document


class PopplerRenderer(render.AbstractRenderer):
    if popplerqt5:
        renderBackend = popplerqt5.Poppler.Document.SplashBackend
        printRenderBackend = popplerqt5.Poppler.Document.SplashBackend
    else:
        renderBackend = printRenderBackend = 0

    oversampleThreshold = 96

    def render(self, page, key, tile, paperColor=None):
        """Generate an image for the Page referred to by key."""
        if paperColor is None:
            paperColor = page.paperColor or self.paperColor

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
            key.rotation, paperColor)
        if multiplier == 2:
            image = image.scaledToWidth(tile.w, Qt.SmoothTransformation)
        image.setDotsPerMeterX(int(xres * 39.37))
        image.setDotsPerMeterY(int(yres * 39.37))
        return image

    def setRenderHints(self, doc):
        """Set the poppler render hints we want to set."""
        if self.antialiasing:
            doc.setRenderHint(popplerqt5.Poppler.Document.Antialiasing)
            doc.setRenderHint(popplerqt5.Poppler.Document.TextAntialiasing)

    @contextlib.contextmanager
    def setup(self, doc, backend=None, paperColor=None):
        """Use the poppler document in context, properly configured and locked."""
        with locking.lock(doc):
            if backend is not None:
                oldbackend = doc.renderBackend()
                doc.setRenderBackend(backend)
            oldhints = int(doc.renderHints())
            doc.setRenderHint(oldhints, False)
            self.setRenderHints(doc)
            if paperColor is not None:
                oldcolor = doc.paperColor()
                doc.setPaperColor(paperColor)
            try:
                yield
            finally:
                if backend is not None:
                    doc.setRenderBackend(oldbackend)
                doc.setRenderHint(int(doc.renderHints()), False)
                doc.setRenderHint(oldhints)
                if paperColor is not None:
                    doc.setPaperColor(oldcolor)

    def render_poppler_image(self, doc, pageNum,
                                   xres=72.0, yres=72.0,
                                   x=-1, y=-1, w=-1, h=-1, rotate=Rotate_0,
                                   paperColor=None):
        """Render an image, almost like calling page.renderToImage().

        The document is properly locked during rendering and render options
        are set.

        """
        with self.setup(doc, self.renderBackend, paperColor):
            return doc.page(pageNum).renderToImage(xres, yres, x, y, w, h, rotate)

    def draw(self, page, painter, key, tile, paperColor=None):
        """Draw a tile on the painter.

        The painter is already at the right position and rotation.
        For the Poppler page and renderer, draw() is only used for printing.
        (See AbstractPage.print().)

        """
        source = self.map(key, page.pageRect()).mapRect(QRectF(*tile)).toRect()   # rounded
        target = QRectF(0, 0, tile.w, tile.h)
        if key.rotation & 1:
            target.setSize(target.size().transposed())

        doc = page.document
        p = doc.page(page.pageNumber)

        with self.setup(doc, self.printRenderBackend, paperColor):
            if self.printRenderBackend == popplerqt5.Poppler.Document.ArthurBackend:
                # Poppler's Arthur backend removes the current transform from
                # the painter (it sets a default CTM, instead of combining it
                # with the current transform). We let Poppler draw on a QPicture,
                # and draw that on our painter.
                pic = QPicture()
                p.renderToPainter(QPainter(pic), page.dpi, page.dpi, source.x(), source.y(), source.width(), source.height())
                # our resolution could be different, scale accordingly
                painter.save()
                painter.scale(pic.logicalDpiX() / painter.device().logicalDpiX(),
                              pic.logicalDpiY() / painter.device().logicalDpiY())
                pic.play(painter)
                painter.restore()
            else:
                # Make an image exactly in the printer's resolution
                m = painter.transform()
                r = m.mapRect(source)       # see where the source ends up
                w, h = r.width(), r.height()
                if m.m11() == 0:
                    w, h = h, w     # swap if rotation & 1  :-)
                # now we know the scale from our dpi to the paintdevice's logicalDpi!
                hscale = w / source.width()
                vscale = h / source.height()
                s = QTransform().scale(hscale, vscale).mapRect(source)
                dpiX = page.dpi * hscale
                dpiY = page.dpi * vscale
                img = p.renderToImage(dpiX, dpiY, s.x(), s.y(), s.width(), s.height())
                painter.drawImage(target, img, QRectF(img.rect()))


def load(source):
    """Load a Poppler document.

    Source may be:
        - a Poppler document, which is then simply returned :-)
        - a filename
        - q QByteArray instance.

    Returns None if popplerqt5 is not available or the document could not be
    loaded.

    """
    if popplerqt5:
        if isinstance(source, popplerqt5.Poppler.Document):
            return source
        elif isinstance(source, str):
            return popplerqt5.Poppler.Document.load(source)
        else:
            return popplerqt5.Poppler.Document.loadFromData(source)



# install a default renderer, so PopplerPage can be used directly
PopplerPage.renderer = PopplerRenderer()



