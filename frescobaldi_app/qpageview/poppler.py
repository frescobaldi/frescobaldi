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

"""

from PyQt5.QtCore import Qt

import popplerqt5

from . import page
from . import locking


def available():
    """Return true if popplerqt5 is available."""
    return popplerqt5 is not None


class PopplerPage(page.AbstractPage):
    def __init__(self, document, pageNumber):
        super().__init__()
        self._document = document
        self._pageNumber = pageNumber
        self._pageSize = document.page(pageNumber).pageSize()
        # TEMP
        self.image = None
        
    def document(self):
        """Returns the document."""
        return self._document
        
    def pageNumber(self):
        """Returns the page number."""
        return self._pageNumber

    def paint(self, painter, dest_rect, source_rect):
        # TEMP
        if not self.image or self.image.size() != self.size():
            self.image = Renderer().image(self)
        painter.drawImage(dest_rect, self.image, source_rect)
        

class Renderer:
    paperColor = None
    renderHint = (
        popplerqt5.Poppler.Document.Antialiasing |
        popplerqt5.Poppler.Document.TextAntialiasing
    )
    renderBackend = popplerqt5.Poppler.Document.SplashBackend
    oversampleThreshold = 96

    def image(self, page):
        """Generate an image."""
        d = page.document()
        p = d.page(page._pageNumber)
        s = p.pageSizeF()
        if page.computedRotation() & 1:
            s.transpose()

        xres = 72.0 * page.width() / s.width()
        yres = 72.0 * page.height() / s.height()
        
        multiplier = 2 if xres < self.oversampleThreshold else 1
        with locking.lock(d):
            if self.renderHint is not None:
                d.setRenderHint(int(d.renderHints()), False)
                d.setRenderHint(self.renderHint)
            if self.paperColor is not None:
                d.setPaperColor(self.paperColor)
            if self.renderBackend is not None:
                d.setRenderBackend(self.renderBackend)
            image = p.renderToImage(
                        xres * multiplier,
                        yres * multiplier,
                        0, 0,
                        page.width() * multiplier,
                        page.height() * multiplier,
                        page.computedRotation())
        
        if multiplier == 2:
            image = image.scaledToWidth(page.width(), Qt.SmoothTransformation)
        return image



