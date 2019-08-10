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
A View mixin class that draws a nice drop shadow around all pages.
"""

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QPainter, QPen


class ShadowViewMixin:
    """Mixin class that draws a drop shadow around every Page."""
    def paintEvent(self, ev):
        layout_pos = self.layoutPosition()
        painter = QPainter(self.viewport())
        
        # pages to paint a shadow around
        ev_rect = ev.rect().translated(-layout_pos)
        pages_to_paint = set(self._pageLayout.pagesAt(ev_rect))
        # paint the shadows
        for page in pages_to_paint:
            painter.save()
            painter.translate(page.pos() + self.layoutPosition())
            self.drawDropShadow(page, painter, self._pageLayout.spacing / 2)
            painter.restore()
        
        super().paintEvent(ev)      # then draw the contents

    def drawDropShadow(self, page, painter, width):
        """Draw a drop shadow of width pixels around the Page.
        
        The painter is already translated to the topleft corner of the Page.
        
        """
        width = round(width)
        rect = page.rect().adjusted(width / 2, width / 2, 0, 0)
        color = QColor(Qt.black)
        pen = QPen()
        pen.setWidth(1)
        pen.setJoinStyle(Qt.MiterJoin)
        for i in range(width):
            color.setAlpha(255**((width-i)/width))
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(-i, -i, i, i))




