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

from PyQt5.QtCore import QIODevice, QSizeF
from PyQt5.QtGui import QPageSize, QPdfWriter


def pdf(filename, pageList, resolution=72, paperColor=None):
    """Export the pages in pageList to a PDF document.
    
    filename can be a string or any QIODevice. Normally vector graphics are
    rendered, but in cases where that is not possible, the resolution will
    be used to determine the DPI for the generated rendering.
    
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


