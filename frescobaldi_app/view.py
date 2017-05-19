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
View is basically a QPlainTextEdit instance.

It is used to edit a Document. The ViewManager (see viewmanager.py)
has support for showing multiple Views in a window.
"""


import weakref

from PyQt5.QtCore import QEvent, QMimeData, QSettings, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QContextMenuEvent, QKeySequence, QPainter, QTextCursor, QCursor)
from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QToolTip

import app
import metainfo
import textformats
import cursortools
import variables
import cursorkeys
import open_file_at_cursor

metainfo.define('auto_indent', True)
metainfo.define('position', 0)


class View(QPlainTextEdit):
    """View is the text editor widget a Document is displayed and edited with.

    It is basically a QPlainTextEdit with some extra features:
    - it draws a grey cursor when out of focus
    - it reads basic palette colors from the preferences
    - it determines tab width from the document variables (defaulting to 8 characters)
    - it stores the cursor position in the metainfo
    - it runs the auto_indenter when enabled (also checked via metainfo)

    """
    def __init__(self, document):
        """Create the View for the given document."""
        super(View, self).__init__()
        # to enable mouseMoveEvent to display tooltip
        super(View, self).setMouseTracking(True)
        self.setDocument(document)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setCursorWidth(2)
        # restore saved cursor position (defaulting to 0)
        document.loaded.connect(self.restoreCursor)
        document.loaded.connect(self.setTabWidth)
        document.closed.connect(self.slotDocumentClosed)
        self.textChanged.connect(self.invalidateCurrentBlock)
        variables.manager(document).changed.connect(self.setTabWidth)
        self.restoreCursor()
        app.settingsChanged.connect(self.readSettings)
        self.readSettings() # will also call updateCursor
        # line wrap preference is only read on init
        wrap = QSettings().value("view_preferences/wrap_lines", False, bool)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth if wrap else QPlainTextEdit.NoWrap)
        self.installEventFilter(cursorkeys.handler)
        self.toolTipInfo = []
        self.block_at_mouse = None
        self.include_target = []
        app.viewCreated(self)

    def event(self, ev):
        """General event handler.

        This is reimplemented to:

        - prevent inserting the hard line separator, which makes no sense in
          plain text

        - prevent handling Undo and Redo, they work better via the menu actions

        - handle Tab and Backtab to change the indent

        """
        if ev in (
                # avoid the line separator, makes no sense in plain text
                QKeySequence.InsertLineSeparator,
                # those can better be called via the menu actions, then they
                # work better
                QKeySequence.Undo,
                QKeySequence.Redo,
            ):
            return False
        # handle Tab and Backtab
        if ev.type() == QEvent.KeyPress:
            cursor = self.textCursor()
            if ev.key() == Qt.Key_Tab and ev.modifiers() == Qt.NoModifier:
                # tab pressed, insert a tab when no selection and in text,
                # else increase the indent
                if not cursor.hasSelection():
                    block = cursor.block()
                    text = block.text()[:cursor.position() - block.position()]
                    if text and not text.isspace():
                        if variables.get(self.document(), 'document-tabs', True):
                            cursor.insertText('\t')
                        else:
                            tabwidth = variables.get(self.document(), 'tab-width', 8)
                            spaces = tabwidth - len(text.expandtabs(tabwidth)) % tabwidth
                            cursor.insertText(' ' * spaces)
                        self.setTextCursor(cursor)
                        return True
                import indent
                indent.increase_indent(cursor)
                if not cursor.hasSelection():
                    cursortools.strip_indent(cursor)
                    self.setTextCursor(cursor)
                return True
            elif ev.key() == Qt.Key_Backtab and ev.modifiers() == Qt.ShiftModifier:
                # shift-tab pressed, decrease the indent
                import indent
                indent.decrease_indent(cursor)
                if not cursor.hasSelection():
                    cursortools.strip_indent(cursor)
                    self.setTextCursor(cursor)
                return True
        return super(View, self).event(ev)

    def keyPressEvent(self, ev):
        """Reimplemented to perform actions after a key has been pressed.

        Currently handles:

        - indent change on Enter, }, # or >
        
        - update the tooltip info when Ctrl is pressed

        """
        super(View, self).keyPressEvent(ev)
        if ev.key() == Qt.Key_Control and self.include_target:
            self.viewport().setCursor(Qt.PointingHandCursor)
        if metainfo.info(self.document()).auto_indent:
            # run the indenter on Return or when the user entered a dedent token.
            import indent
            cursor = self.textCursor()
            if ev.text() == '\r' or (ev.text() in ('}', '#', '>') and indent.indentable(cursor)):
                indent.auto_indent_block(cursor.block())
                # fix subsequent vertical moves
                cursor.setPosition(cursor.position())
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

    def gotoTextCursor(self, cursor, numlines=3):
        """Go to the specified cursor.

        If possible, at least numlines (default: 3) number of surrounding lines
        is shown. The number of surrounding lines can also be set in the
        preferences, under the key "view_preferences/context_lines". This
        setting takes precedence.

        """
        numlines = QSettings().value("view_preferences/context_lines", numlines, int)
        if numlines > 0:
            c = QTextCursor(cursor)
            c.setPosition(cursor.selectionEnd())
            c.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, numlines)
            self.setTextCursor(c)
            c.setPosition(cursor.selectionStart())
            c.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor, numlines)
            self.setTextCursor(c)
        self.setTextCursor(cursor)

    def readSettings(self):
        """Read preferences and adjust to those.

        Called on init and when app.settingsChanged fires.
        Sets colors, font and tab width from the preferences.

        """
        data = textformats.formatData('editor')
        self.setFont(data.font)
        self.setPalette(data.palette())
        self.setTabWidth()

    def slotDocumentClosed(self):
        """Store the current cursor position in a document on close"""
        if self.hasFocus():
            self.storeCursor()

    def restoreCursor(self):
        """Place the cursor on the position saved in metainfo."""
        cursor = QTextCursor(self.document())
        cursor.setPosition(metainfo.info(self.document()).position)
        self.setTextCursor(cursor)
        QTimer.singleShot(0, self.ensureCursorVisible)

    def storeCursor(self):
        """Stores our cursor position in the metainfo."""
        metainfo.info(self.document()).position = self.textCursor().position()

    def setTabWidth(self):
        """(Internal) Read the tab-width variable and the font settings to set the tabStopWidth."""
        tabwidth = QSettings().value("indent/tab_width", 8, int)
        tabwidth = self.fontMetrics().width(" ") * variables.get(self.document(), 'tab-width', tabwidth)
        self.setTabStopWidth(tabwidth)

    def contextMenuEvent(self, ev):
        """Called when the user requests the context menu."""
        cursor = self.textCursor()
        if ev.reason() == QContextMenuEvent.Mouse:
            # if clicked inside the selection, retain it, otherwise de-select
            # and move the cursor to the clicked position
            pos = self.mapToGlobal(ev.pos())
            clicked = self.cursorForPosition(ev.pos())
            if not cursor.selectionStart() <= clicked.position() < cursor.selectionEnd():
                self.setTextCursor(clicked)
        else:
            pos = self.viewport().mapToGlobal(self.cursorRect().center())
        import contextmenu
        menu = contextmenu.contextmenu(self)
        menu.popup(pos)
        menu.setFocus() # so we get a FocusOut event and the grey cursor gets painted
        menu.exec_()
        menu.deleteLater()

    def mousePressEvent(self, ev):
        """Called when a mouse button is clicked."""
        # implements ctrl-click
        if ev.button() == Qt.LeftButton and ev.modifiers() == Qt.ControlModifier:
            cursor = self.textCursor()
            clicked = self.cursorForPosition(ev.pos())
            if cursor.selectionStart() <= clicked.position() < cursor.selectionEnd():
                clicked = cursor
            # include files?
            if self.include_target:
                import open_file_at_cursor
                open_file_at_cursor.open_targets(self.window(), self.include_target)
                return
            # go to definition?
            import definition
            if definition.goto_definition(self.window(), clicked):
                return
        super(View, self).mousePressEvent(ev)

    def invalidateCurrentBlock(self):
        """Make sure that tooltip info is recalculated after document changes"""
        self.block_at_mouse = None

    def mouseMoveEvent(self, ev):
        """Track the mouse move to show the tooltip"""
        super(View, self).mouseMoveEvent(ev)
        cursor_at_mouse = self.cursorForPosition(ev.pos())
        cur_block = cursor_at_mouse.block()
        # Only check tooltip when changing line/block or after invalidating
        if self.include_target or not cur_block == self.block_at_mouse:
            self.block_at_mouse = cur_block
            self.include_target = open_file_at_cursor.includeTarget(cursor_at_mouse)
            if self.include_target:
                if ev.modifiers() == Qt.ControlModifier:
                   self.viewport().setCursor(QCursor(Qt.PointingHandCursor))
                self.showIncludeToolTip()
            else:
                self.include_target = []
                self.block_at_mouse = None
                self.viewport().setCursor(Qt.IBeamCursor)
                QToolTip.hideText()

    def showIncludeToolTip(self):
        """Show a tooltip with the currently determined include target"""
        QToolTip.showText(QCursor.pos(), '\n'.join(self.include_target))

    def createMimeDataFromSelection(self):
        """Reimplemented to only copy plain text."""
        m = QMimeData()
        m.setText(self.textCursor().selection().toPlainText())
        return m
