# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Code to use LilyPond-generated SVGs as icons.
The default black color will be adjusted to the default Text color.
"""

import os

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication, QIcon, QIconEngineV2, QPainter, QPixmap, QStyleOption
from PyQt4.QtSvg import QSvgRenderer

__all__ = ["icon"]


_icons = {}
_alpha = {}
_pixmaps = {}


def icon(name):
    """Returns a QIcon that shows a LilyPond-generated SVG in the default text color."""
    try:
        return _icons[name]
    except KeyError:
        icon = _icons[name] = QIcon(Engine(name))
        return icon


def alpha(name, size):
    """Returns a (possibly cached) alpha pixmap from a LilyPond symbol."""
    key = (name, size.width(), size.height())
    try:
        return _alpha[key]
    except KeyError:
        p = QPixmap(size)
        p.fill(Qt.transparent)
        r = QSvgRenderer(os.path.join(__path__[0], name + ".svg"))
        r.render(QPainter(p))
        a = _alpha[key] = p.alphaChannel()
        return a


def pixmap(name, size, mode, state):
    """Returns a pixmap of the name and size with the default text color.
    
    The state argument is ignored for now.
    
    """
    key = (name, size.width(), size.height(), mode, id(QApplication.style()))
    try:
        return _pixmaps[key]
    except KeyError:
        p = QPixmap(size)
        p.fill(QApplication.palette().foreground().color())
        p.setAlphaChannel(alpha(name, size))
        p = _pixmaps[key] = QApplication.style().generatedIconPixmap(mode, p, QStyleOption())
        return p


class Engine(QIconEngineV2):
    """Engine to provide renderings of SVG icons in the default text color."""
    def __init__(self, name):
        super(Engine, self).__init__()
        self._name = name
        
    def pixmap(self, size, mode, state):
        return pixmap(self._name, size, mode, state)
        
    def paint(self, painter, rect, mode, state):
        p = self.pixmap(rect.size(), mode, state)
        painter.drawPixmap(rect, p)
        

