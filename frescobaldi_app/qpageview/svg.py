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
A page that can display a SVG document.

"""

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtSvg import QSvgRenderer

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)

from . import page

class SvgPage(page.AbstractPage):
    """A page that can display a SVG document."""
    paperColor = QColor(Qt.white)
    
    def __init__(self, load_file=None):
        self.renderer = QSvgRenderer()
        if load_file:
            self.load(load_file)
    
    def load(self, load_file):
        """Load filename or QByteArray."""
        if self.renderer.load(load_file):
            self.pageWidth = self.renderer.defaultSize().width()
            self.pageHeight = self.renderer.defaultSize().height()
        
    def paint(self, painter, rect, callback=None):
        #TODO rotation
        painter.fillRect(rect, self.paperColor)
        self.renderer.render(painter, QRectF(0, 0, self.pageWidth, self.pageHeight))

