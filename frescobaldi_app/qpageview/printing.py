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


from PyQt5.QtGui import QPainter, QTransform


def printPages(printer, pageList):
    """TEMP. Prints pages at 100% size on printer."""
    
    printer.setFullPage(True)
    painter = QPainter(printer)
    
    for n, page in enumerate(pageList):
        if n:
            printer.newPage()
        
        r = printer.pageRect()
        
        painter.save()
        
        m = QTransform()
        
        m.translate(r.center().x(), r.center().y())
        m.scale(printer.logicalDpiX() / page.dpi, printer.logicalDpiY() / page.dpi)
        m.rotate(page.rotation * 90)
        m.scale(page.scaleX, page.scaleY)
        m.translate(page.pageWidth / -2, page.pageHeight / -2)
        
        painter.setTransform(m, True)
        page.print(painter)
        painter.restore()
        
    return painter.end()


