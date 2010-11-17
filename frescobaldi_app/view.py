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
The View is basically a QPlainTextEditor instance with a status bar.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import icons


class View(QWidget):
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.editor = QPlainTextEdit(self)
        layout.addWidget(self.editor)
        
        slayout = QHBoxLayout()
        slayout.setContentsMargins(0, 0, 0, 0)
        slayout.setSpacing(2)
        layout.addLayout(slayout)
        
        self.pos = QLabel()
        slayout.addWidget(self.pos)
        
        self.state = QLabel()
        self.state.setFixedSize(QSize(16, 16))
        slayout.addWidget(self.state)
        
        self.info = QLabel()
        slayout.addWidget(self.info, 1)
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(16)
        slayout.addWidget(self.progress, 1)
        
        self.editor.cursorPositionChanged.connect(self.updateStatusBar)
        self.editor.modificationChanged.connect(self.updateStatusBar)
        
        self.updateStatusBar()
        
    def document(self):
        return self.editor.document()
        
    def textCursor(self):
        return self.editor.textCursor()

    def updateStatusBar(self):
        cur = self.editor.textCursor()
        self.pos.setText(_("Line: {line}, Col: {column}").format(
            line = cur.blockNumber() + 1,
            column = cur.columnNumber()))
        if self.editor.document().isModified():
            self.state.setPixmap(icons.get('document-save').pixmap(16))
        else:
            self.state.setText('')
            
            
        
        