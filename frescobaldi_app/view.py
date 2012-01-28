# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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

It is used to edit a Document. The ViewManager (see viewmanager.py)
has support for showing multiple Views in a window.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt4.QtGui import (
    QApplication, QKeySequence, QPainter, QPlainTextEdit, QTextCursor)

import app
import homekey
import metainfo
import textformats
import cursortools
import variables


metainfo.define('autoindent', True)
metainfo.define('position', 0)


class View(QPlainTextEdit):
    """View is the text editor widget a Document is displayed and edited with.
    
    It is basically a QPlainTextEdit with some extra features:
    - it draws a grey cursor when out of focus
    - it reads basic palette colors from the preferences
    - it determines tab width from the document variables (defaulting to 8 characters)
    - it stores the cursor position in the metainfo
    - it runs the autoindenter when enabled (also checked via metainfo)
    - it can display a widget in the bottom using showWidget and hideWidget.
    
    """
    def __init__(self, document):
        """Creates the View for the given document."""
        super(View, self).__init__()
        self._widget = None
        self.setDocument(document)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setCursorWidth(2)
        # restore saved cursor position (defaulting to 0)
        document.loaded.connect(self.restoreCursor)
        document.loaded.connect(self.setTabWidth)
        document.closed.connect(self.slotDocumentClosed)
        variables.manager(document).changed.connect(self.setTabWidth)
        self.restoreCursor()
        app.settingsChanged.connect(self.readSettings)
        self.readSettings() # will also call updateCursor
        app.viewCreated(self)
        
    def showWidget(self, widget):
        """Displays the widget in the bottom of the View."""
        widget.setParent(self)
        self._widget = widget
        self.updateWidgetPosition()
    
    def hideWidget(self, widget):
        """Removes the widget from the bottom of the View."""
        widget.setParent(None)
        self._widget = None
        self.setViewportMargins(0, 0, 0, 0)
    
    def updateWidgetPosition(self):
        """Moves and resizes the widget embedded with showWidget()."""
        geom = self.viewport().geometry()
        height = self._widget.heightForWidth(geom.width())
        if height == -1:
            height = self._widget.sizeHint().height()
        geom.translate(0, geom.height())
        geom.setHeight(height)
        self._widget.setGeometry(geom)
        self.setViewportMargins(0, 0, 0, height)
    
    def resizeEvent(self, ev):
        """Reimplemented to re-position widget embedded with showWidget()."""
        super(View, self).resizeEvent(ev)
        if self._widget:
            self.updateWidgetPosition()
        
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
        if homekey.handle(self, ev):
            return
        super(View, self).keyPressEvent(ev)
        
        if metainfo.info(self.document()).autoindent:
            # run the indenter on Return or when the user entered a dedent token.
            import indent
            cursor = self.textCursor()
            if ev.text() == '\r' or (ev.text() in ('}', '#', '>') and indent.indentable(cursor)):
                with cursortools.editBlock(cursor, True):
                    indent.autoIndentBlock(cursor.block())
                # keep the cursor at the indent position on vertical move
                cursor = self.textCursor()
                pos = cursor.position()
                cursor.setPosition(cursor.block().position()) # move horizontal
                cursor.setPosition(pos) # move back to position
                self.setTextCursor(cursor)
            
    def focusOutEvent(self, ev):
        """Reimplemented to store the cursor position on focus out."""
        super(View, self).focusOutEvent(ev)
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

    def paintEvent(self, ev):
        """Reimplemented to paint a cursor if we have no focus."""
        super(View, self).paintEvent(ev)
        if not self.hasFocus():
            rect = self.cursorRect()
            if rect.intersects(ev.rect()):
                color = self.palette().text().color()
                color.setAlpha(128)
                QPainter(self.viewport()).fillRect(rect, color)
    
    def readSettings(self):
        data = textformats.formatData('editor')
        self.setFont(data.font)
        self.setPalette(data.palette())
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

    def setTabWidth(self):
        """(Internal) Reads the tab-width variable and the font settings to set the tabStopWidth."""
        tabwidth = self.fontMetrics().width(" ") * variables.get(self.document(), 'tab-width', 8)
        self.setTabStopWidth(tabwidth)


