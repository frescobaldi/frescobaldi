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
A widget to enter a keyboard shortcut.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
)

class KeySequenceWidget(QWidget):

    keySequenceChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super(KeySequenceWidget, self).__init__(parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)
        
        self.button = KeySequenceButton(self)
        self.clearButton = QToolButton(self)
        self.clearButton.setIcon(icons.get("edit-clear-locationbar-rtl"))
        layout.addWidget(self.button)
        layout.addWidget(self.clearButton)
        
        self.button.clicked.connect(self.keySequenceChanged) # TEMP
        self.clearButton.clicked.connect(self.clear)
        self.translateUI()
        
    def translateUI(self):
        self.clearButton.setToolTip(_("Click to clear the key sequence."))
        
    def setShortcut(self, shortcut):
        """Sets the initial shortcut to display."""
        self.button.setKeySequence(shortcut)
        
    def clear(self):
        """Empties the displayed shortcut."""
        if not self.button.keySequence().isEmpty():
            self.button.setKeySequence(QKeySequence())
            self.keySequenceChanged.emit()


class KeySequenceButton(QPushButton):
    
    def __init__(self, parent=None):
        super(KeySequenceButton, self).__init__(parent)
        self.setIcon(icons.get("edit-configure"))
        self._seq = QKeySequence()
        
    def setKeySequence(self, seq):
        self._seq = seq
        self.setText(seq.toString())

    def keySequence(self):
        return self._seq
        