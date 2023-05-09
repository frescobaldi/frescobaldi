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
A View mixin class that draws a nice drop shadow around all pages.
"""

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QPainter, QPen


class ShadowViewMixin:
    """Mixin class that draws a drop shadow around every Page.

    Drawing the drop shadow can be turned off by setting dropShadowEnabled
    to False.

    """

    dropShadowEnabled = True

    def paintEvent(self, ev):
        if self.dropShadowEnabled:
            width = round(self._pageLayout.spacing / 2.0)
            # make the rect slightly larger, so we "see" shadow of pages that
            # would be outside view normally.
            rect = ev.rect().adjusted(-width, -width, width // 2, width // 2)
            painter = QPainter(self.viewport())
            for page, rect in self.pagesToPaint(rect, painter):
                self.drawDropShadow(page, painter, width)
        super().paintEvent(ev)      # then draw the contents

    def drawDropShadow(self, page, painter, width):
        """Draw a drop shadow of width pixels around the Page.

        The painter is already translated to the topleft corner of the Page.

        """
        width = round(width)
        rect = page.rect().adjusted(width // 2, width // 2, 0, 0)
        color = QColor(Qt.black)
        pen = QPen()
        pen.setWidth(1)
        pen.setJoinStyle(Qt.MiterJoin)
        for i in range(width):
            f = (width-i)/width
            color.setAlpha(int(200**f + 55*f))
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(-i, -i, i, i))




