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

from PyQt4.QtCore import QFile, QIODevice
from PyQt4.QtGui import QPrinter

from .locking import lock


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


