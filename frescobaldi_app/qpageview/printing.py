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
Printing facilities for qpageview.
"""


from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPainter, QTransform

from . import util


class PrintJob(util.BackgroundJob):
    """Performs a print job in the background.

    Emits:

    progress(pageNumber, num, total)        # before each Page
    finished()                              # when done

    """
    progress = pyqtSignal(int, int, int)

    aborted = False

    def __init__(self, printer, pageList, parent=None):
        """Initialize with a QPrinter object and a list of pages.

        pageList may be a list of two-tuples (num, page). Otherwise, the pages
        are numbered from 1 in the progress message. The pages are copied.

        """
        super().__init__(parent)
        self.printer = printer
        self.setPageList(pageList)

    def setPageList(self, pageList):
        """Set the pagelist to print.

        pageList may be a list of two-tuples (num, page). Otherwise, the pages
        are numbered from 1 in the progress message. The pages are copied.

        """
        self.pageList = []
        for n, page in enumerate(pageList, 1):
            if isinstance(page, tuple):
                pageNum, page = page
            else:
                pageNum = n
            page = page.copy()
            # set zoom to 1.0 so computations based on geometry() are
            # accurate enough
            page.updateSize(page.dpi, page.dpi, 1.0)
            self.pageList.append((pageNum, page))

    def work(self):
        """Paint the pages to the printer in the background."""
        p = self.printer
        p.setFullPage(True)
        painter = QPainter(p)
        for n, (num, page) in enumerate(self.pageList):
            if self.isInterruptionRequested():
                self.aborted = True
                return p.abort()
            self.progress.emit(num, n+1, len(self.pageList))
            if n:
                p.newPage()
            painter.save()
            # center on the page and use scale 100% (TEMP)
            r = p.pageRect()
            m = QTransform()
            m.translate(r.center().x(), r.center().y())
            m.scale(p.logicalDpiX() / page.dpi, p.logicalDpiY() / page.dpi)
            m.rotate(page.rotation * 90)
            m.scale(page.scaleX, page.scaleY)
            m.translate(page.pageWidth / -2, page.pageHeight / -2)
            painter.setTransform(m, True)
            page.print(painter)
            painter.restore()
        return painter.end()


