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

from PyQt4.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt4.QtGui import (
    QApplication, QColor, QPainter, QPalette, QPlainTextEdit, QTextCursor,
    QTextEdit, QTextFormat, QVBoxLayout)

import app
import metainfo
import textformats
import bookmarks
import tokeniter
import variables


metainfo.define('autoindent', True)
metainfo.define('position', 0)


class View(QPlainTextEdit):
    
    focusIn = pyqtSignal()
    
    def __init__(self, document):
        super(View, self).__init__()
        self._paintcursor = False
        self._markedLineExtraSelections = []
        self._matchExtraSelections = []
        self._matchTimer = QTimer(singleShot=True, interval=1000, timeout=self.clearMatches)
        self._searchExtraSelections = []
        self._cursorExtraSelection = QTextEdit.ExtraSelection()
        self._cursorExtraSelection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.setDocument(document)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setCursorWidth(2)
        # restore saved cursor position (defaulting to 0)
        document.loaded.connect(self.restoreCursor)
        document.loaded.connect(self.setTabWidth)
        document.closed.connect(self.slotDocumentClosed)
        bookmarks.bookmarks(document).marksChanged.connect(self.updateMarkedLines)
        variables.manager(document).changed.connect(self.setTabWidth)
        self.restoreCursor()
        self.cursorPositionChanged.connect(self.updateCursor)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings() # will also call updateCursor and updateMarkedLines
        
        # layout to show widgets in bottom
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignBottom)
        self.setLayout(layout)
        
    def readSettings(self):
        data = textformats.formatData('editor')
        self.setFont(data.font)
        p = QApplication.palette()
        p.setColor(QPalette.Text, data.baseColors['text'])
        p.setColor(QPalette.Base, data.baseColors['background'])
        p.setColor(QPalette.HighlightedText, data.baseColors['selectiontext'])
        p.setColor(QPalette.Highlight, data.baseColors['selectionbackground'])
        self.setPalette(p)
        self._baseColors = data.baseColors
        self.updateMarkedLines()
        self.updateCursor()
        self.setTabWidth()
        
    def setTabWidth(self):
        tabwidth = self.fontMetrics().width(" ") * variables.get(self.document(), 'tab-width', 8)
        self.setTabStopWidth(tabwidth)
        
    def focusInEvent(self, ev):
        super(View, self).focusInEvent(ev)
        self.updateCursor()
        self.focusIn.emit()
        self._paintcursor = False
        
    def focusOutEvent(self, ev):
        super(View, self).focusOutEvent(ev)
        self.updateCursor()
        self.storeCursor()
        self._paintcursor = True # display the textcursor even if we have no focus

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

    def paintEvent(self, ev):
        super(View, self).paintEvent(ev)
        if self._paintcursor:
            rect = self.cursorRect()
            if rect.intersects(ev.rect()):
                color = self.palette().text().color()
                color.setAlpha(128)
                QPainter(self.viewport()).fillRect(rect, color)
        
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
        es = self._cursorExtraSelection
        es.cursor = self.textCursor()
        es.cursor.clearSelection()
        color = QColor(self._baseColors['current'])
        color.setAlpha(200 if self.hasFocus() else 100)
        es.format.setBackground(color)
        self.updateExtraSelections()
        
    def updateMarkedLines(self):
        lines = self._markedLineExtraSelections = []
        for type, marks in bookmarks.bookmarks(self.document()).marks().items():
            for mark in marks:
                es = QTextEdit.ExtraSelection()
                es.cursor = mark
                color = QColor(self._baseColors[type])
                color.setAlpha(200)
                es.format.setBackground(color)
                es.format.setProperty(QTextFormat.FullWidthSelection, True)
                lines.append(es)
        self.updateExtraSelections()
        
    def updateExtraSelections(self):
        extraSelections = (
            self._markedLineExtraSelections +
            [self._cursorExtraSelection] +
            self._searchExtraSelections +
            self._matchExtraSelections
        )
        self.setExtraSelections(extraSelections)
    
    def setSearchResults(self, cursors):
        results = self._searchExtraSelections = []
        for cursor in cursors:
            es = QTextEdit.ExtraSelection()
            es.cursor = cursor
            es.format.setBackground(self._baseColors['search'])
            results.append(es)
        self.updateExtraSelections()
    
    def setMatches(self, cursors, type = 'match'):
        matches = self._matchExtraSelections = []
        for cursor in cursors:
            es = QTextEdit.ExtraSelection()
            es.cursor = cursor
            es.format.setBackground(self._baseColors[type])
            matches.append(es)
        self.updateExtraSelections()
        self._matchTimer.start()

    def clearMatches(self):
        self._matchExtraSelections = []
        self.updateExtraSelections()
        
    def showWidget(self, widget):
        """Displays the widget in the bottom of the View."""
        self.setViewportMargins(0, 0, 0, widget.height())
        self.layout().addWidget(widget)
    
    def hideWidget(self, widget):
        """Removes the widget from the bottom of the View."""
        self.layout().removeWidget(widget)
        self.setViewportMargins(0, 0, 0, 0)

    def keyPressEvent(self, ev):
        super(View, self).keyPressEvent(ev)
        
        if metainfo.info(self.document()).autoindent:
            # run the indenter on Return or when the user entered a dedent token.
            import indent
            cursor = self.textCursor()
            if ev.text() == '\r' or (ev.text() in ('}', '#', '>') and indent.indentable(cursor)):
                with tokeniter.editBlock(cursor, True):
                    indent.autoIndentBlock(cursor.block())
            
    def event(self, ev):
        # handle Tab and Backtab
        if ev.type() == QEvent.KeyPress:
            modifiers = int(ev.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
            if ev.key() == Qt.Key_Tab and modifiers == 0:
                import indent
                indent.increaseIndent(self.textCursor())
                return True
            elif ev.key() == Qt.Key_Backtab and modifiers & ~Qt.SHIFT == 0:
                import indent
                indent.decreaseIndent(self.textCursor())
                return True
        return super(View, self).event(ev)


