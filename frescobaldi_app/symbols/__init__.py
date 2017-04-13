# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
Code to use LilyPond-generated SVGs as icons.
The default black color will be adjusted to the default Text color.
"""


import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QIconEngine, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QStyleOption
from PyQt5.QtSvg import QSvgRenderer

__all__ = ["icon"]


_icons = {}
_pixmaps = {}


def icon(name):
    """Returns a QIcon that shows a LilyPond-generated SVG in the default text color."""
    try:
        return _icons[name]
    except KeyError:
        icon = _icons[name] = QIcon(Engine(name))
        return icon


def pixmap(name, size, mode, state):
    """Returns a (possibly cached) pixmap of the name and size with the default text color.

    The state argument is ignored for now.

    """
    if mode == QIcon.Selected:
        color = QApplication.palette().highlightedText().color()
    else:
        color = QApplication.palette().text().color()
    key = (name, size.width(), size.height(), color.rgb(), mode)
    try:
        return _pixmaps[key]
    except KeyError:
        i = QImage(size, QImage.Format_ARGB32_Premultiplied)
        i.fill(0)
        painter = QPainter(i)
        # render SVG symbol
        QSvgRenderer(os.path.join(__path__[0], name + ".svg")).render(painter)
        # recolor to text color
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(i.rect(), color)
        painter.end()
        # let style alter the drawing based on mode, and create QPixmap
        pixmap = QApplication.style().generatedIconPixmap(mode, QPixmap.fromImage(i), QStyleOption())
        _pixmaps[key] = pixmap
        return pixmap


class Engine(QIconEngine):
    """Engine to provide renderings of SVG icons in the default text color."""
    def __init__(self, name):
        super(Engine, self).__init__()
        self._name = name

    def pixmap(self, size, mode, state):
        return pixmap(self._name, size, mode, state)

    def paint(self, painter, rect, mode, state):
        p = self.pixmap(rect.size(), mode, state)
        painter.drawPixmap(rect, p)


