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
View is basically a QPlainTextEdit instance.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import metainfo
import textformats


class View(QPlainTextEdit):
    
    focusIn = pyqtSignal(QPlainTextEdit)
    
    def __init__(self, document):
        super(View, self).__init__()
        self.setDocument(document)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setCursorWidth(2)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        # restore saved cursor position (defaulting to 0)
        document.loaded.connect(self.restoreCursor)
        document.closed.connect(self.slotDocumentClosed)
        self.restoreCursor()
        self.cursorPositionChanged.connect(self.updateCursor)
        self.updateCursor()
    
    def readSettings(self):
        s = QSettings()
        s.beginGroup("Editor")
        
        data = textformats.textFormatData()
        self.setFont(data.font)
        metrics = QFontMetrics(data.font)
        tabwidth = metrics.width(" ") * int(s.value("tabwidth", 8))
        self.setTabStopWidth(tabwidth)
        
        p = QApplication.palette()
        p.setColor(QPalette.Text, data.baseColors['text'])
        p.setColor(QPalette.Base, data.baseColors['background'])
        p.setColor(QPalette.HighlightedText, data.baseColors['selectiontext'])
        p.setColor(QPalette.Highlight, data.baseColors['selectionbackground'])
        self.setPalette(p)
        self._currentLineColor = data.baseColors['current']
        
    def focusInEvent(self, ev):
        super(View, self).focusInEvent(ev)
        self.updateCursor()
        self.focusIn.emit(self)
        
    def focusOutEvent(self, ev):
        super(View, self).focusOutEvent(ev)
        self.updateCursor()
        self.storeCursor()

    def dragEnterEvent(self, ev):
        """Reimplemented to avoid showing the cursor when dropping URLs."""
        if ev.mimeData().hasUrls():
            ev.accept()
        else:
            super(View, self).dragEnterEvent(ev)
        
    def dragMoveEvent(self, ev):
        """Reimplemented to avoid showing the cursor when dropping URLs."""
        if ev.mimeData().hasUrls():
            ev.accept()
        else:
            super(View, self).dragMoveEvent(ev)
        
    def dropEvent(self, ev):
        """Called when something is dropped.
        
        Calls dropEvent() of MainWindow if URLs are dropped.
        
        """
        if ev.mimeData().hasUrls():
            self.window().dropEvent(ev)
        else:
            super(View, self).dropEvent(ev)

    def slotDocumentClosed(self):
        if self.hasFocus():
            self.storeCursor()
            
    def restoreCursor(self):
        """Places the cursor on the position saved in metainfo."""
        cursor = QTextCursor(self.document())
        cursor.setPosition(metainfo.info(self.document()).position)
        self.setTextCursor(cursor)
        QTimer.singleShot(0, self.ensureCursorVisible)
    
    def storeCursor(self):
        """Stores our cursor position in the metainfo."""
        metainfo.info(self.document()).position = self.textCursor().position()

    def updateCursor(self):
        """Called when the textCursor has moved."""
        # highlight current line
        es = QTextEdit.ExtraSelection()
        es.cursor = self.textCursor()
        es.cursor.clearSelection()
        color = QColor(self._currentLineColor)
        self.hasFocus() or color.setAlpha(100)
        es.format.setBackground(color)
        es.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.setExtraSelections([es])
        



