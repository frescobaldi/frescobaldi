# -*- coding: utf-8 -*-
#
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
Export Pages to different file formats.
"""

import os

from PyQt5.QtCore import QBuffer, QIODevice, QMimeData, QPoint, QSizeF, Qt, QUrl
from PyQt5.QtGui import QDrag, QGuiApplication, QImage, QPageSize, QPdfWriter

from . import poppler
from . import util


class AbstractExporter:
    """Base class to export a rectangular area of a Page to a file.

    Specialized subclasses implement each format.

    You instantiate a subclass with a Page and a rectangle. The rectangle may
    be None, to specify the full page. After instantiation, you can set
    attributes to configure the export. The following attributes are supported::

        resolution = 300
        autocrop = False
        oversample = 1
        grayscale = False
        paperColor = None
        forceVector = True  # force the render backend to be Arthur for
                            # exporting PDF pages to vector-based formats

    After setting the attributes, you call one or more of save(), copyData(),
    copyFile(), mimeData() or tempFileMimeData(), which will trigger the export
    because they internally call data(), which caches its return value until
    setPage() is called again.

    Not all exporters support all attributes, the supportXXX attributes specify
    whether an attribute is supported or not.

    """
    # user settings:
    resolution = 300
    antialiasing = True
    autocrop = False
    oversample = 1
    grayscale = False
    paperColor = None
    forceVector = True  # force the render backend to be Arthur for PDF pages

    # properties of exporter:
    wantsVector = True
    supportsResolution = True
    supportsAntialiasing = True
    supportsAutocrop = True
    supportsOversample = True
    supportsGrayscale = True
    supportsPaperColor = True

    mimeType = "application/octet-stream"
    filename = ""
    defaultBasename = "document"
    defaultExt = ""

    def __init__(self, page, rect=None):
        self.setPage(page, rect)

    def setPage(self, page, rect=None):
        self._page = page.copy()
        if self._page.renderer:
            self._page.renderer = page.renderer.copy()
        self._rect = rect
        self._result = None   # where the exported object is stored
        self._tempFile = None
        self._autoCropRect = None
        self._document = None
        self._pixmap = None

    def page(self):
        """Return our page, setting the renderer to our preferences."""
        p = self._page.copy()
        p.paperColor = self.paperColor
        if self._page.renderer:
            p.renderer = self._page.renderer.copy()
            p.renderer.paperColor = self.paperColor
            p.renderer.antialiasing = self.antialiasing
            if self.forceVector and self.wantsVector and \
                    isinstance(p, poppler.PopplerPage) and poppler.popplerqt5:
                p.renderer.printRenderBackend = \
                    poppler.popplerqt5.Poppler.Document.ArthurBackend
        return p

    def autoCroppedRect(self):
        """Return the rect, autocropped if desired."""
        if not self.autocrop:
            return self._rect
        if self._autoCropRect is None:
            p = self._page
            dpiX = p.width / p.defaultSize().width() * p.dpi
            dpiY = p.height / p.defaultSize().height() * p.dpi
            image = p.image(self._rect, dpiX, dpiY)
            rect = util.autoCropRect(image)
            # add one pixel to prevent loosing small joins or curves etc
            rect = image.rect() & rect.adjusted(-1, -1, 1, 1)
            if self._rect is not None:
                rect.translate(self._rect.topLeft())
            self._autoCropRect = rect
        return self._autoCropRect

    def export(self):
        """Perform the export, based on the settings, and return the exported data object."""

    def successful(self):
        """Return True when export was successful."""
        return self.data() is not None

    def data(self):
        """Return the export result, assuming it is binary data of the exported file."""
        if self._result is None:
            self._result = self.export()
        return self._result

    def document(self):
        """Return a one-page Document to display the image to export.

        Internally calls createDocument(), and caches the result, setting the
        papercolor to the papercolor attribute if the exporter supports
        papercolor.

        """
        if self._document is None:
            doc = self._document = self.createDocument()
            if self.paperColor and self.paperColor.isValid():
                for p in doc.pages():
                    p.paperColor = self.paperColor
        return self._document

    def createDocument(self):
        """Create and return a one-page Document to display the image to export."""

    def renderer(self):
        """Return a renderer for the document(). By default, None is returned."""
        return None

    def copyData(self):
        """Copy the QMimeData() to the clipboard."""
        QGuiApplication.clipboard().setMimeData(self.mimeData())

    def mimeData(self):
        """Return a QMimeData() object representing the exported data."""
        data = QMimeData()
        data.setData(self.mimeType, self.data())
        return data

    def save(self, filename):
        """Save the exported image to a file."""
        with open(filename, "wb") as f:
            f.write(self.data())

    def suggestedFilename(self):
        """Return a suggested file name for the file to export.

        The name is based on the filename (if set) and also contains the
        directory path. But the name will never be the same as the filename
        set in the filename attribute.

        """
        if self.filename:
            base = os.path.splitext(self.filename)[0]
            name = base + self.defaultExt
            if name == self.filename:
                name = base + "-export" + self.defaultExt
        else:
            name = self.defaultBasename + self.defaultExt
        return name

    def tempFilename(self):
        """Save data() to a tempfile and returns the filename."""
        if self._tempFile is None:
            if self.filename:
                basename = os.path.splitext(os.path.basename(self.filename))[0]
            else:
                basename = self.defaultBasename
            d = util.tempdir()
            fname = self._tempFile = os.path.join(d, basename + self.defaultExt)
            self.save(fname)
        return self._tempFile

    def tempFileMimeData(self):
        """Save the exported image to a temp file and return a QMimeData object for the url."""
        data = QMimeData()
        data.setUrls([QUrl.fromLocalFile(self.tempFilename())])
        return data

    def copyFile(self):
        """Save the exported image to a temp file and copy its name to the clipboard."""
        QGuiApplication.clipboard().setMimeData(self.tempFileMimeData())

    def pixmap(self, size=100):
        """Return a small pixmap to use for dragging etc."""
        if self._pixmap is None:
            paperColor = self.paperColor if self.supportsPaperColor else None
            page = self.document().pages()[0]
            self._pixmap = page.pixmap(paperColor=paperColor)
        return self._pixmap

    def drag(self, parent, mimeData):
        """Called by dragFile and dragData. Execs a QDrag on the mime data."""
        d = QDrag(parent)
        d.setMimeData(mimeData)
        d.setPixmap(self.pixmap())
        d.setHotSpot(QPoint(-10, -10))
        return d.exec_(Qt.CopyAction)

    def dragData(self, parent):
        """Start dragging the data. Parent can be any QObject."""
        return self.drag(parent, self.mimeData())

    def dragFile(self, parent):
        """Start dragging the data. Parent can be any QObject."""
        return self.drag(parent, self.tempFileMimeData())


class ImageExporter(AbstractExporter):
    """Export a rectangular area of a Page (or the whole page) to an image."""
    wantsVector = False
    defaultBasename = "image"
    defaultExt = ".png"

    def export(self):
        """Create the QImage representing the exported image."""
        res = self.resolution
        if self.oversample != 1:
            res *= self.oversample
        i = self.page().image(self._rect, res, res, self.paperColor)
        if self.oversample != 1:
            i = i.scaled(i.size() / self.oversample, transformMode=Qt.SmoothTransformation)
        if self.grayscale:
            i = i.convertToFormat(QImage.Format_Grayscale8)
        if self.autocrop:
            i = i.copy(util.autoCropRect(i))
        return i

    def image(self):
        return self.data()

    def createDocument(self):
        from . import image
        return image.ImageDocument([self.image()], self.renderer())

    def copyData(self):
        QGuiApplication.clipboard().setImage(self.image())

    def mimeData(self):
        data = QMimeData()
        data.setImageData(self.image())
        return data

    def save(self, filename):
        if not self.image().save(filename):
            raise OSError("Could not save image")


class SvgExporter(AbstractExporter):
    """Export a rectangular area of a Page (or the whole page) to a SVG file."""
    mimeType = "image/svg"
    supportsGrayscale = False
    supportsOversample = False
    defaultBasename = "image"
    defaultExt = ".svg"

    def export(self):
        rect = self.autoCroppedRect()
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        success = self.page().svg(buf, rect, self.resolution, self.paperColor)
        buf.close()
        if success:
            return buf.data()

    def createDocument(self):
        from . import svg
        return svg.SvgDocument([self.data()], self.renderer())


class PdfExporter(AbstractExporter):
    """Export a rectangular area of a Page (or the whole page) to a PDF file."""
    mimeType = "application/pdf"
    supportsGrayscale = False
    supportsOversample = False
    defaultExt = ".pdf"

    def export(self):
        rect = self.autoCroppedRect()
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        success = self.page().pdf(buf, rect, self.resolution, self.paperColor)
        buf.close()
        if success:
            return buf.data()

    def createDocument(self):
        from . import poppler
        return poppler.PopplerDocument(self.data(), self.renderer())


class EpsExporter(AbstractExporter):
    """Export a rectangular area of a Page (or the whole page) to an EPS file."""
    mimeType = "application/postscript"
    supportsGrayscale = False
    supportsOversample = False
    defaultExt = ".eps"

    def export(self):
        rect = self.autoCroppedRect()
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        success = self.page().eps(buf, rect, self.resolution, self.paperColor)
        buf.close()
        if success:
            return buf.data()

    def createDocument(self):
        from . import poppler
        rect = self.autoCroppedRect()
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        success = self.page().pdf(buf, rect, self.resolution, self.paperColor)
        buf.close()
        return poppler.PopplerDocument(buf.data(), self.renderer())


def pdf(filename, pageList, resolution=72, paperColor=None):
    """Export the pages in pageList to a PDF document.

    filename can be a string or any QIODevice. The pageList is a list of the
    Page objects to export.

    Normally vector graphics are rendered, but in cases where that is not
    possible, the resolution will be used to determine the DPI for the
    generated rendering.

    The computedRotation attribute of the pages is used to determine the
    rotation.

    Make copies of the pages if you run this function in a background thread.

    """
    pdf = QPdfWriter(filename)
    pdf.setCreator("qpageview")
    pdf.setResolution(resolution)

    for n, page in enumerate(pageList):
        # map to the original page
        source = page.pageRect()
        # scale to target size
        w = source.width() * page.scaleX
        h = source.height() * page.scaleY
        if page.computedRotation & 1:
            w, h = h, w
        targetSize = QSizeF(w, h)
        if n:
            pdf.newPage()
        layout = pdf.pageLayout()
        layout.setMode(layout.FullPageMode)
        layout.setPageSize(QPageSize(targetSize * 72.0 / page.dpi, QPageSize.Point))
        pdf.setPageLayout(layout)
        # TODO handle errors?
        page.output(pdf, source, paperColor)


