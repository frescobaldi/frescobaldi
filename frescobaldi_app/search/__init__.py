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
Widget for search and replace.
"""


import bisect
import re
import weakref

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QKeySequence, QPalette, QTextCursor
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QGridLayout, QLabel, QLineEdit,
    QPushButton, QStyle, QToolButton, QWidget)

import app
import icons
import qutil
import plugin
import userguide
import cursortools
import textformats
import wordboundary
import viewhighlighter
import gadgets.borderlayout


class Search(plugin.MainWindowPlugin, QWidget):
    def __init__(self, mainwindow):
        QWidget.__init__(self, mainwindow)
        self._currentView = None
        self._positions = []
        self._positionsDirty = True
        self._replace = False  # are we in replace mode?
        self._going = False    # are we moving the text cursor?

        mainwindow.currentViewChanged.connect(self.viewChanged)
        mainwindow.actionCollection.edit_find_next.triggered.connect(self.findNext)
        mainwindow.actionCollection.edit_find_previous.triggered.connect(self.findPrevious)

        # don't inherit looks from view
        self.setFont(QApplication.font())
        self.setPalette(QApplication.palette())

        grid = QGridLayout(spacing=2)
        grid.setContentsMargins(4, 0, 4, 0)
        grid.setVerticalSpacing(0)
        self.setLayout(grid)

        self.searchEntry = QLineEdit(textChanged=self.slotSearchChanged)
        self.searchLabel = QLabel()
        self.prevButton = QToolButton(autoRaise=True, focusPolicy=Qt.NoFocus, clicked=self.findPrevious)
        self.prevButton.setIcon(icons.get('go-previous'))
        self.nextButton = QToolButton(autoRaise=True, focusPolicy=Qt.NoFocus, clicked=self.findNext)
        self.nextButton.setIcon(icons.get('go-next'))
        self.caseCheck = QCheckBox(checked=True, focusPolicy=Qt.NoFocus)
        self.regexCheck = QCheckBox(focusPolicy=Qt.NoFocus)
        self.countLabel = QLabel(alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.countLabel.setMinimumWidth(QApplication.fontMetrics().width("9999"))
        self.closeButton = QToolButton(autoRaise=True, focusPolicy=Qt.NoFocus)
        self.hideAction = QAction(self, triggered=self.slotHide)
        self.hideAction.setShortcut(QKeySequence(Qt.Key_Escape))
        self.hideAction.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.closeButton.setDefaultAction(self.hideAction)

        grid.addWidget(self.searchLabel, 0, 0)
        grid.addWidget(self.searchEntry, 0, 1)
        grid.addWidget(self.prevButton, 0, 2)
        grid.addWidget(self.nextButton, 0, 3)
        grid.addWidget(self.caseCheck, 0, 4)
        grid.addWidget(self.regexCheck, 0, 5)
        grid.addWidget(self.countLabel, 0, 6)
        grid.addWidget(self.closeButton, 0, 7)

        self.caseCheck.toggled.connect(self.slotSearchChanged)
        self.regexCheck.toggled.connect(self.slotSearchChanged)

        self.replaceEntry = QLineEdit()
        self.replaceLabel = QLabel()
        self.replaceButton = QPushButton(clicked=self.slotReplace)
        self.replaceAllButton = QPushButton(clicked=self.slotReplaceAll)

        grid.addWidget(self.replaceLabel, 1, 0)
        grid.addWidget(self.replaceEntry, 1, 1)
        grid.addWidget(self.replaceButton, 1, 4)
        grid.addWidget(self.replaceAllButton, 1, 5)

        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        app.translateUI(self)

    def translateUI(self):
        self.searchLabel.setText(_("Search:"))
        self.prevButton.setToolTip(_("Find Previous"))
        self.nextButton.setToolTip(_("Find Next"))
        self.caseCheck.setText(_("&Case"))
        self.caseCheck.setToolTip(_("Case Sensitive"))
        self.regexCheck.setText(_("&Regex"))
        self.regexCheck.setToolTip(_("Regular Expression"))
        self.countLabel.setToolTip(_("The total number of matches"))
        self.hideAction.setToolTip(_("Close"))
        self.replaceLabel.setText(_("Replace:"))
        self.replaceButton.setText(_("Re&place"))
        self.replaceButton.setToolTip(_("Replaces the next occurrence of the search term."))
        self.replaceAllButton.setText(_("&All"))
        self.replaceAllButton.setToolTip(_("Replaces all occurrences of the search term in the document or selection."))

    def readSettings(self):
        data = textformats.formatData('editor')
        self.searchEntry.setFont(data.font)
        self.replaceEntry.setFont(data.font)
        p = data.palette()
        self.searchEntry.setPalette(p)
        self.replaceEntry.setPalette(p)

    def currentView(self):
        """Return the currently active View."""
        return self._currentView and self._currentView()

    def setCurrentView(self, view):
        """Set the currently active View, called by showWidget()."""
        cur = self.currentView()
        if cur:
            cur.selectionChanged.disconnect(self.slotSelectionChanged)
            cur.document().contentsChanged.disconnect(self.slotDocumentContentsChanged)
        if view:
            view.selectionChanged.connect(self.slotSelectionChanged)
            view.document().contentsChanged.connect(self.slotDocumentContentsChanged)
        self._currentView = weakref.ref(view) if view else None

    def showWidget(self):
        """Show the search widget and connect with the active View."""
        if self.isVisible():
            self.hideWidget()
        view = self.window().currentView()
        self.setCurrentView(view)
        layout = gadgets.borderlayout.BorderLayout.get(view)
        layout.addWidget(self, gadgets.borderlayout.BOTTOM)
        self.show()

    def hideWidget(self):
        """Hide the widget, but remain connected with the active View."""
        view = self.currentView()
        if view:
            self.highlightingOff()
            self.hide()
            layout = gadgets.borderlayout.BorderLayout.get(view)
            layout.removeWidget(self)

    def viewChanged(self, new):
        """Called when the user switches to another View."""
        self.setParent(None)
        self.hideWidget()
        self.setCurrentView(new)
        self.markPositionsDirty()

    def slotSelectionChanged(self):
        """Called when the user changes the selection."""
        if not self._going:
            self.markPositionsDirty()
            if self.isVisible():
                self.updatePositions()
                self.highlightingOn()

    def slotDocumentContentsChanged(self):
        """Called when the current document changes."""
        self.markPositionsDirty()
        if self.isVisible():
            self.updatePositions()
            self.highlightingOn()

    def slotHide(self):
        """Called when the close button is clicked."""
        view = self.currentView()
        if view:
            self.hideWidget()
            view.setFocus()

    def find(self):
        """Called by the main menu Find... command."""
        # hide replace stuff
        self.replaceLabel.hide()
        self.replaceEntry.hide()
        self.replaceButton.hide()
        self.replaceAllButton.hide()
        self._replace = False # we are not in replace mode
        visible = self.isVisible()
        if not visible:
            self.showWidget()
        else:
            self.adjustSize()
        cursor = self.currentView().textCursor()
        #if not visible and self.currentView():
        if cursor.hasSelection():
            word = cursor.selection().toPlainText()
            if not re.search(r'\w', word):
                word = ""
            elif self.regexCheck.isChecked():
                word = re.escape(word)
            with qutil.signalsBlocked(self.searchEntry):
                self.searchEntry.setText(word)
            self.slotSearchChanged()
        else:
            self.searchEntry.selectAll()
            self.highlightingOn()
        self.searchEntry.setFocus()

    def replace(self):
        """Called by the main menu Find and Replace... command."""
        # show replace stuff
        self.replaceLabel.show()
        self.replaceEntry.show()
        self.replaceButton.show()
        self.replaceAllButton.show()
        focus = self.replaceEntry if self.isVisible() and self.searchEntry.text() else self.searchEntry
        self._replace = True # we are in replace mode
        if self.isVisible():
            self.adjustSize()
        else:
            self.showWidget()
            self.markPositionsDirty()
            self.updatePositions()
            self.highlightingOn()
        focus.setFocus()

    def slotSearchChanged(self):
        """Called on every change in the search text entry."""
        self._going = True
        self.markPositionsDirty()
        self.updatePositions()
        self.highlightingOn()
        if not self._replace and self._positions:
            positions = [c.position() for c in self._positions]
            cursor = self.currentView().textCursor()
            index = bisect.bisect_left(positions, cursor.selectionStart())
            if index == len(positions):
                index -= 1
            elif index > 0:
                # it might be possible that the text cursor currently already
                # is in a search result. This happens when the search is pop up
                # with an empty text and the current word is then set as search
                # text.
                if cursortools.contains(self._positions[index-1], cursor):
                    index -= 1
            self.gotoPosition(index)
        self._going = False

    def highlightingOn(self, view=None):
        """Show the current search result positions."""
        if view is None:
            view = self.currentView()
        if view:
            viewhighlighter.highlighter(view).highlight("search", self._positions, 1)

    def highlightingOff(self, view=None):
        """Hide the current search result positions."""
        if view is None:
            view = self.currentView()
        if view:
            viewhighlighter.highlighter(view).clear("search")

    def markPositionsDirty(self):
        """Delete positions and mark them dirty, i.e. they need updating."""
        self._positions = []
        self._positionsDirty = True

    def updatePositions(self):
        """Update the search result positions if necessary."""
        view = self.currentView()
        if not view or not self._positionsDirty:
            return
        search = self.searchEntry.text()
        cursor = view.textCursor()
        document = view.document()
        self._positions = []
        if search:
            text = document.toPlainText()
            start = 0
            if (self._replace or not self._going) and cursor.hasSelection():
                # don't search outside the selection
                start = cursor.selectionStart()
                text = text[start:cursor.selectionEnd()]
            flags = re.MULTILINE | re.DOTALL
            if not self.caseCheck.isChecked():
                flags |= re.IGNORECASE
            if not self.regexCheck.isChecked():
                search = re.escape(search)
            try:
                matches = re.finditer(search, text, flags)
            except re.error:
                pass
            else:
                for m in matches:
                    c = QTextCursor(document)
                    c.setPosition(start + m.end())
                    c.setPosition(start + m.start(), QTextCursor.KeepAnchor)
                    self._positions.append(c)
        self.countLabel.setText(format(len(self._positions)))
        enabled = len(self._positions) > 0
        self.replaceButton.setEnabled(enabled)
        self.replaceAllButton.setEnabled(enabled)
        self.prevButton.setEnabled(enabled)
        self.nextButton.setEnabled(enabled)
        self._positionsDirty = False

    def findNext(self):
        """Called on menu Find Next."""
        self._going = True
        self.updatePositions()
        view = self.currentView()
        if view and self._positions:
            positions = [c.position() for c in self._positions]
            index = bisect.bisect_right(positions, view.textCursor().position())
            if index < len(positions):
                self.gotoPosition(index)
            else:
                self.gotoPosition(0)
            view.ensureCursorVisible()
        self._going = False

    def findPrevious(self):
        """Called on menu Find Previous."""
        self._going = True
        self.updatePositions()
        view = self.currentView()
        positions = [c.position() for c in self._positions]
        if view and positions:
            index = bisect.bisect_left(positions, view.textCursor().position()) - 1
            self.gotoPosition(index)
        self._going = False

    def gotoPosition(self, index):
        """Scrolls the current View to the position in the _positions list at index."""
        c = QTextCursor(self._positions[index])
        #c.clearSelection()
        self.currentView().gotoTextCursor(c)
        self.currentView().ensureCursorVisible()

    def event(self, ev):
        """Reimplemented to catch F1 for help and Tab so it does not reach the View."""
        if ev == QKeySequence.HelpContents:
            userguide.show("search_replace")
            ev.accept()
            return True
        elif ev.type() == QEvent.KeyPress:
            modifiers = int(ev.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
            if ev.key() == Qt.Key_Tab and modifiers == 0:
                # prevent Tab from reaching the View widget
                self.window().focusNextChild()
                ev.accept()
                return True
            elif ev.key() == Qt.Key_Backtab and modifiers & ~Qt.SHIFT == 0:
                # prevent Tab from reaching the View widget
                self.window().focusPreviousChild()
                ev.accept()
                return True
        return super(Search, self).event(ev)

    def keyPressEvent(self, ev):
        """Catches Up and Down to jump between search results."""
        # if in search mode, Up and Down jump between search results
        if not self._replace and self._positions and self.searchEntry.text() and not ev.modifiers():
            if ev.key() == Qt.Key_Up:
                self.findPrevious()
                return
            elif ev.key() ==  Qt.Key_Down:
                self.findNext()
                return
        # use enter or return for search next
        if ev.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.findNext()
            return
        super(Search, self).keyPressEvent(ev)

    def doReplace(self, cursor):
        """Perform one replace action."""
        text = cursor.selection().toPlainText()
        search = self.searchEntry.text()
        replace = self.replaceEntry.text()
        ok = text == search
        if self.regexCheck.isChecked():
            m = re.match(search, text)
            ok = False
            if m:
                try:
                    replace = m.expand(replace)
                    ok = True
                except re.error:
                    pass
        if ok:
            pos = cursor.position()
            cursor.insertText(replace)
            cursor.setPosition(pos, QTextCursor.KeepAnchor)
        return ok

    def slotReplace(self):
        """Called when the user clicks Replace."""
        view = self.currentView()
        if view and self._positions:
            positions = [c.position() for c in self._positions]
            index = bisect.bisect_left(positions, view.textCursor().position())
            if index >= len(positions):
                index = 0
            if self.doReplace(self._positions[index]):
                self.findNext()

    def slotReplaceAll(self):
        """Called when the user clicks Replace All."""
        view = self.currentView()
        if view:
            replaced = False
            cursors = self._positions
            if view.textCursor().hasSelection():
                cursors = [cursor for cursor in cursors if cursortools.contains(view.textCursor(), cursor)]
            with cursortools.compress_undo(view.textCursor()):
                for cursor in cursors:
                    if self.doReplace(cursor):
                        replaced = True
            if replaced:
                self.highlightingOn()


