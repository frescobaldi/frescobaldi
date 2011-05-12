# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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
Utility functions.
"""

from PyQt4.QtCore import QFile, QIODevice, QObject, Qt, pyqtSignal
from PyQt4.QtGui import QColor, QPainter, QPrinter

from .locking import lock
from .render import RenderOptions


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
                raise ValueError, "invalid page number: {0}".format(num)
    
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


class Printer(QObject):
    """Prints a Poppler.Document to a QPrinter.
    
    This is currently done using raster images at max. 300DPI,
    because the ArthurBackend of Poppler (that can render to a painter)
    does not work correctly in all cases and is not well supported by
    the Poppler developers at this time.
    
    """
    printing = pyqtSignal(int, int, int)
    
    def __init__(self, document, printer, parent=None):
        """Creates the Printer instance.
        
        document: a Poppler.Document
        printer: a QPrinter
        
        """
        QObject.__init__(self, parent)
        self.document = document
        self.printer = printer
        self._stop = False
    
    def pageList(self):
        """Returns a list of desired page numbers (starting with 1)."""
        p = self.printer
        if (p.printRange() == QPrinter.AllPages
            or (p.fromPage() == 0 and p.toPage() == 0)):
            pages = range(1, self.document.numPages() + 1)
        else:
            pages = range(max(p.fromPage(), 1), min(p.toPage(), self.document.numPages()) + 1)
        return list(pages)
    
    def print_(self):
        """Prints the document."""
        p = self.printer
        p.setFullPage(True)
        p.setResolution(300)
        
        center = p.paperRect().center()
        painter = QPainter(p)
        
        pages  = self.pageList()
        if p.pageOrder() != QPrinter.FirstPageFirst:
            pages.reverse()

        total = len(pages)
        
        opts = RenderOptions()
        opts.setRenderHint(0)
        opts.setPaperColor(QColor(Qt.white))
        
        for num, pageNum in enumerate(pages, 1):
            self.progress(num, total, pageNum)
            if self._stop:
                return p.abort()
            
            with lock(self.document):
                opts.write(self.document)
                page = self.document.page(pageNum - 1)
                img = page.renderToImage(300, 300)
            rect = img.rect()
            rect.moveCenter(center)
            painter.drawImage(rect, img)
            
            if num != total:
                p.newPage()
        return painter.end()
        
    def cancel(self):
        """Instructs the printer to cancel."""
        self._stop = True

    def progress(self, num, total, pageNumber):
        """Called when printing a page.
        
        num: counts the pages (starts with 1)
        total: the total number of pages
        pageNumber: the page number in the document (starts also with 1)
        
        The default implementation emits the printing() signal.
        
        """
        self.printing.emit(num, total, pageNumber)
    

