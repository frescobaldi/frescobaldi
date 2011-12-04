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
The special characters tool widget.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import widgets.charmap
import unicode_blocks
import listmodel


class Widget(QWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
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
        
        model = listmodel.ListModel(unicode_blocks.blocks(),
            display = lambda b: b.name)
        self.blockCombo.setModel(model)
        
        # load block setting
        name = QSettings().value("charmaptool/last_block", "")
        if name:
            for i, b in enumerate(unicode_blocks.blocks()):
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
        family = s.value("fontfamily", "")
        if family:
            font.setFamily(family)
        self.charmap.charmap.setDisplayFont(font)
        size = float(s.value("fontsize", font.pointSizeF()))
        self.charmap.charmap.setDisplayFontSizeF(size)
    
    def updateBlock(self):
        i = self.blockCombo.currentIndex()
        if 0 <= i < len(unicode_blocks.blocks()):
            first, last, name = unicode_blocks.blocks()[i]
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



