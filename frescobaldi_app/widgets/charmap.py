# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Provides a widget displaying characters from a font.

When a character is clicked, a signal is emitted.

"""

from __future__ import unicode_literals


from PyQt4.QtCore import *
from PyQt4.QtGui import *


class CharMap(QWidget):
    def __init__(self, parent=None):
        super(CharMap, self).__init__(parent)
        self._column_count = 32
        self._square = 24
        self._range = (0, 0)
        self._font = QFont()
        
    def setRange(self, first, last):
        self._range = (first, last)
        self.adjustSize()
        self.update()
    
    def range(self):
        return self._range
    
    def square(self):
        """Returns the width of one item (determined by font size)."""
        return self._square
        
    def setDisplayFont(self, font):
        self._font.setFamily(font.family())
        self.update()
    
    def displayFont(self):
        return QFont(self._font)
    
    def setDisplayFontSize(self, size):
        self._font.setPointSize(size)
        self._square = max(24, QFontMetrics(self._font).xHeight() * 3)
        self.adjustSize()
        self.update()
    
    def setColumnCount(self, count):
        """Sets how many columns should be used."""
        count = max(1, count)
        self._column_count = count
        self.adjustSize()
        self.update()
    
    def columnCount(self):
        return self._column_count
        
    def sizeHint(self):
        first, last = self._range
        rows = ((last - first) // self._column_count) + 1
        return QSize(self._column_count, rows) * self._square

