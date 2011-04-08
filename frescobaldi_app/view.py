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
View is basically a QPlainTextEdit instance.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt4.QtGui import (
    QApplication, QColor, QPainter, QPalette, QPlainTextEdit, QTextCharFormat, QTextCursor,
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
        self._selections = {}
        self._cursorFormat = QTextCharFormat()
        self._cursorFormat.setProperty(QTextFormat.FullWidthSelection, True)
        self._paintcursor = False
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
        self.readSettings() # will also call updateCursor
        self.updateMarkedLines()
        
        # layout to show widgets in bottom
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignBottom)
        self.setLayout(layout)
        
    def showWidget(self, widget):
        """Displays the widget in the bottom of the View."""
        self.setViewportMargins(0, 0, 0, widget.height())
        self.layout().addWidget(widget)
    
    def hideWidget(self, widget):
        """Removes the widget from the bottom of the View."""
        self.layout().removeWidget(widget)
        self.setViewportMargins(0, 0, 0, 0)

    def highlight(self, format, cursors, priority, msec=0):
        """Highlights the selection of an arbitrary list of QTextCursors.
        
        format can be a name for a predefined text format or a QTextCharFormat.
        priority determines the order of drawing, highlighting with higher priority
        is drawn over highlighting with lower priority.
        msec, if > 0, removes the highlighting after that many milliseconds.
        
        """
        fmt = format if isinstance(format, QTextFormat) else self.textFormat(format)
        selections = []
        for cursor in cursors:
            es = QTextEdit.ExtraSelection()
            es.cursor = cursor
            es.format = fmt
            selections.append(es)
        if msec:
            def clear(selfref=weakref.ref(self)):
                self = selfref()
                if self:
                    self.clearHighlight(format)
            timer = QTimer(timeout=clear, singleShot=True)
            timer.start(msec)
            self._selections[format] = (priority, selections, timer)
        else:
            self._selections[format] = (priority, selections)
        self.updateHighlighting()
        
    def clearHighlight(self, format):
        """Removes the highlighting for the given format (name or QTextCharFormat)."""
        try:
            del self._selections[format]
        except KeyError:
            pass
        else:
            self.updateHighlighting()

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

    def keyPressEvent(self, ev):
        super(View, self).keyPressEvent(ev)
        
        if metainfo.info(self.document()).autoindent:
            # run the indenter on Return or when the user entered a dedent token.
            import indent
            cursor = self.textCursor()
            if ev.text() == '\r' or (ev.text() in ('}', '#', '>') and indent.indentable(cursor)):
                with tokeniter.editBlock(cursor, True):
                    indent.autoIndentBlock(cursor.block())
            
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
        # paint a cursor if we have no focus
        super(View, self).paintEvent(ev)
        if self._paintcursor:
            rect = self.cursorRect()
            if rect.intersects(ev.rect()):
                color = self.palette().text().color()
                color.setAlpha(128)
                QPainter(self.viewport()).fillRect(rect, color)
        
    def readSettings(self):
        data = textformats.formatData('editor')
        self.setFont(data.font)
        self.setPalette(data.palette())
        self._baseColors = data.baseColors
        self.reloadHighlighting()
        self.updateCursor()
        self.setTabWidth()
        
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
        color = QColor(self._baseColors['current'])
        color.setAlpha(200 if self.hasFocus() else 100)
        self._cursorFormat.setBackground(color)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.highlight(self._cursorFormat, [cursor], 0)
        
    def setTabWidth(self):
        tabwidth = self.fontMetrics().width(" ") * variables.get(self.document(), 'tab-width', 8)
        self.setTabStopWidth(tabwidth)
        
    def updateMarkedLines(self):
        for type, marks in bookmarks.bookmarks(self.document()).marks().items():
            self.highlight(type, marks, -1)
        
    def updateHighlighting(self):
        self.setExtraSelections(sum((s[1] for s in sorted(self._selections.values())), []))

    def textFormat(self, name):
        f = QTextCharFormat()
        f.setBackground(self._baseColors[name])
        if name in ('current', 'mark', 'error'):
            f.setProperty(QTextFormat.FullWidthSelection, True)
        return f
            
    def reloadHighlighting(self):
        """Reloads the named formats in the highlighting (e.g. in case of settings change)."""
        for format in self._selections:
            if not isinstance(format, QTextFormat):
                fmt = self.textFormat(format)
                for es in self._selections[format][1]:
                    es.format = fmt
        self.updateHighlighting()

