# This file is part of the qpopplerview package.
#
# Copyright (c) 2010 - 2014 by Wilbert Berendsen
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
Printing functionality.
"""

from PyQt5.QtCore import QFile, QIODevice, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtPrintSupport import QPrinter

from .locking import lock
from . import render


def psfile(doc, printer, output, pageList=None, margins=(0, 0, 0, 0)):
    """Writes a PostScript rendering of a Poppler::Document to the output.

    doc: a Poppler::Document instance
    printer: a QPrinter instance from which the papersize is read
    output: a filename or opened QIODevice (will not be closed)
    pageList: a list of page numbers. By default the pagerange is read
        from the QPrinter instance. Page numbers start with 1.
    margins: a sequence of four values describing the margins (left, top, right,
        bottom) in Point (1/72 inch), all defaulting to 0.

    Returns True on success, False on error.

    """
    if pageList is None:
        if (printer.printRange() == QPrinter.AllPages
            or (printer.fromPage() == 0 and printer.toPage() == 0)):
            pageList = list(range(1, doc.numPages() + 1))
        else:
            pageList = list(range(max(printer.fromPage(), 1), min(printer.toPage(), doc.numPages()) + 1))
    else:
        for num in pageList:
            if num < 1 or num > doc.numPages():
                raise ValueError("invalid page number: {0}".format(num))

    ps = doc.psConverter()
    ps.setPageList(pageList)

    if isinstance(output, QIODevice):
        ps.setOutputDevice(output)
    else:
        ps.setOutputFileName(output)

    paperSize = printer.paperSize(QPrinter.Point)
    ps.setPaperHeight(paperSize.height())
    ps.setPaperWidth(paperSize.width())

    left, top, right, bottom = margins
    ps.setLeftMargin(left)
    ps.setTopMargin(top)
    ps.setRightMargin(right)
    ps.setBottomMargin(bottom)

    with lock(doc):
        return ps.convert()


class Printer(object):
    """Prints a Poppler.Document to a QPrinter.

    This is currently done using raster images at (by default) 300 DPI,
    because the Arthur backend of Poppler (that can render to a painter)
    does not work correctly in all cases and is not well supported by
    the Poppler developers at this time.

    """
    def __init__(self):
        self._stop = False
        self._resolution = 300
        self._document = None
        self._printer = None
        opts = render.RenderOptions()
        opts.setRenderHint(0)
        opts.setPaperColor(QColor(Qt.white))
        self.setRenderOptions(opts)

    def setDocument(self, document):
        """Sets the Poppler.Document to print (mandatory)."""
        self._document = document

    def document(self):
        """Returns the previously set Poppler.Document."""
        return self._document

    def setPrinter(self, printer):
        """Sets the QPrinter to print to (mandatory)."""
        self._printer = printer

    def printer(self):
        """Returns the previously set QPrinter."""
        return self._printer

    def setResolution(self, dpi):
        """Sets the resolution in dots per inch."""
        self._resolution = dpi

    def resolution(self):
        """Returns the resolution in dots per inch."""
        return self._resolution

    def setRenderOptions(self, options):
        """Sets the render options (see render.py)."""
        self._renderoptions = options

    def renderOptions(self):
        """Returns the render options (see render.py).

        By default, all antialiasing is off and the papercolor is white.

        """
        return self._renderoptions

    def pageList(self):
        """Should return a list of desired page numbers (starting with 1).

        The default implementation reads the pages from the QPrinter.

        """
        p = self.printer()
        if (p.printRange() == QPrinter.AllPages
            or (p.fromPage() == 0 and p.toPage() == 0)):
            pages = range(1, self.document().numPages() + 1)
        else:
            pages = range(max(p.fromPage(), 1), min(p.toPage(), self.document().numPages()) + 1)
        return list(pages)

    def print_(self):
        """Prints the document."""
        self._stop = False
        resolution = self.resolution()
        p = self.printer()
        p.setFullPage(True)
        p.setResolution(resolution)

        center = p.paperRect().center()
        painter = QPainter(p)

        pages  = self.pageList()
        if p.pageOrder() != QPrinter.FirstPageFirst:
            pages.reverse()

        total = len(pages)

        opts = self.renderOptions()
        document = self.document()

        for num, pageNum in enumerate(pages, 1):
            if self._stop:
                return p.abort()
            self.progress(num, total, pageNum)
            if num > 1:
                p.newPage()
            with lock(document):
                opts.write(document)
                page = document.page(pageNum - 1)
                img = page.renderToImage(resolution, resolution)
            rect = img.rect()
            rect.moveCenter(center)
            painter.drawImage(rect, img)

        return painter.end()

    def abort(self):
        """Instructs the printer to cancel the job."""
        self._stop = True

    def aborted(self):
        """Returns whether abort() was called."""
        return self._stop

    def progress(self, num, total, pageNumber):
        """Called when printing a page.

        num: counts the pages (starts with 1)
        total: the total number of pages
        pageNumber: the page number in the document (starts also with 1)

        The default implementation does nothing.

        """
        pass


