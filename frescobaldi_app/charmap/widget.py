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
The special characters tool widget.
"""


import sys
import itertools

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (QComboBox, QScrollArea, QSizePolicy, QVBoxLayout,
                             QWidget)

import app
import widgets.charmap
import unicode_blocks
import listmodel


# avoid handling characters above 0xFFFF in narrow Python builds
_blocks = tuple(itertools.takewhile(
    lambda block: block.end < sys.maxunicode,
        unicode_blocks.blocks()))


class Widget(QWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.blockCombo = QComboBox()
        self.charmap = CharMapWidget()

        layout.addWidget(self.blockCombo)
        layout.addWidget(self.charmap)

        # size policy of combo
        p = self.blockCombo.sizePolicy()
        p.setHorizontalPolicy(QSizePolicy.Ignored)
        self.blockCombo.setSizePolicy(p)

        # size policy of combo popup
        p = self.blockCombo.view().sizePolicy()
        p.setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        self.blockCombo.view().setSizePolicy(p)

        model = listmodel.ListModel(_blocks,
            display = lambda b: b.name)
        self.blockCombo.setModel(model)

        # load block setting
        name = QSettings().value("charmaptool/last_block", "", str)
        if name:
            for i, b in enumerate(_blocks):
                if b.name == name:
                    self.blockCombo.setCurrentIndex(i)
                    break

        self.blockCombo.activated[int].connect(self.updateBlock)
        self.updateBlock()

        self.loadSettings()
        app.settingsChanged.connect(self.loadSettings)

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("charmaptool")
        font = self.font()
        family = s.value("fontfamily", "", str)
        if family:
            font.setFamily(family)
        self.charmap.charmap.setDisplayFont(font)
        size = s.value("fontsize", font.pointSizeF(), float)
        self.charmap.charmap.setDisplayFontSizeF(size)

    def updateBlock(self):
        i = self.blockCombo.currentIndex()
        if 0 <= i < len(_blocks):
            first, last, name = _blocks[i]
            self.charmap.charmap.setRange(first, last)
            QSettings().setValue("charmaptool/last_block", name)





class CharMapWidget(QScrollArea):
    def __init__(self, parent=None):
        super(CharMapWidget, self).__init__(parent)
        self.charmap = widgets.charmap.CharMap()
        self.setWidget(self.charmap)
        # TEMP
        self.charmap.setRange(32, 1023)
        self.charmap.setColumnCount(8)

    def resizeEvent(self, ev):
        self.charmap.setColumnCount(
            self.charmap.columnCountForWidth(ev.size().width()))



