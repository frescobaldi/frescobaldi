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
Widget for search and replace.
"""

import bisect
import re
import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import util


class Search(QWidget):
    def __init__(self, mainwindow):
        super(Search, self).__init__(mainwindow)
        self._currentView = None
        self._positions = None
        self._replace = False  # are we in replace mode?
        
        mainwindow.currentViewChanged.connect(self.viewChanged)
        
        hide = QAction(self, triggered=self.escapePressed)
        hide.setShortcut(QKeySequence(Qt.Key_Escape))
        self.addAction(hide)

        mainwindow.actionCollection.edit_find_next.triggered.connect(self.findNext)
        mainwindow.actionCollection.edit_find_previous.triggered.connect(self.findPrevious)
        
        # dont inherit looks from view
        self.setFont(QApplication.font())
        self.setPalette(QApplication.palette())
        
        grid = QGridLayout()
        grid.setContentsMargins(4, 0, 4, 0)
        grid.setVerticalSpacing(0)
        self.setLayout(grid)
        
        self.searchEntry = QLineEdit(textChanged=self.slotSearchChanged)
        self.searchLabel = QLabel()
        self.caseCheck = QCheckBox()
        self.caseCheck.setChecked(True)
        self.regexCheck = QCheckBox()
        self.countLabel = QLabel()
        self.countLabel.setMinimumWidth(QApplication.fontMetrics().width("9999"))
        self.countLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        grid.addWidget(self.searchLabel, 0, 0)
        grid.addWidget(self.searchEntry, 0, 1)
        grid.addWidget(self.caseCheck, 0, 2)
        grid.addWidget(self.regexCheck, 0, 3)
        grid.addWidget(self.countLabel, 0, 4)
        
        self.caseCheck.toggled.connect(self.slotSearchChanged)
        self.regexCheck.toggled.connect(self.slotSearchChanged)
        self.caseCheck.setFocusPolicy(Qt.NoFocus)
        self.regexCheck.setFocusPolicy(Qt.NoFocus)
        
        self.replaceEntry = QLineEdit()
        self.replaceLabel = QLabel()
        self.replaceButton = QPushButton(clicked=self.slotReplace)
        self.replaceAllButton = QPushButton(clicked=self.slotReplaceAll)
        
        grid.addWidget(self.replaceLabel, 1, 0)
        grid.addWidget(self.replaceEntry, 1, 1)
        grid.addWidget(self.replaceButton, 1, 2)
        grid.addWidget(self.replaceAllButton, 1, 3)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.searchLabel.setText(_("Search:"))
        self.caseCheck.setText(_("&Case"))
        self.caseCheck.setToolTip(_("Case Sensitive"))
        self.regexCheck.setText(_("&Regex"))
        self.regexCheck.setToolTip(_("Regular Expression"))
        self.countLabel.setToolTip(_("The total number of matches"))
        self.replaceLabel.setText(_("Replace:"))
        self.replaceButton.setText(_("Re&place"))
        self.replaceButton.setToolTip(_("Replaces the next occurrence of the search term."))
        self.replaceAllButton.setText(_("&All"))
        self.replaceAllButton.setToolTip(_("Replaces all occurrences of the search term in the document or selection."))
        
    def currentView(self):
        return self._currentView and self._currentView()
    
    def setCurrentView(self, view):
        self._currentView = weakref.ref(view) if view else None
        
    def showWidget(self):
        if self.isVisible():
            self.hideWidget()
        view = self.window().currentView()
        self.setFixedHeight(self.sizeHint().height())
        view.showWidget(self)
        self.setCurrentView(view)
        
        # make the search entry mimic the view's palette
        self.searchEntry.setFont(view.font())
        self.searchEntry.setPalette(view.palette())
        self.replaceEntry.setFont(view.font())
        self.replaceEntry.setPalette(view.palette())
        
        self.show()
        
    def hideWidget(self):
        view = self.currentView()
        if view:
            view.setSearchResults([])
            view.hideWidget(self)
            self.hide()
    
    def viewChanged(self, new):
        self.setParent(None)
        self.hideWidget()
        self.setCurrentView(new)
        self.updatePositions()
        
    def escapePressed(self):
        view = self.currentView()
        if view:
            self.hideWidget()
            view.setFocus()
        
    def find(self):
        # hide replace stuff
        self.replaceLabel.hide()
        self.replaceEntry.hide()
        self.replaceButton.hide()
        self.replaceAllButton.hide()
        self._replace = False # we are not in replace mode
        if not self.isVisible():
            with util.signalsBlocked(self.searchEntry):
                self.searchEntry.clear()
        self.showWidget()
        self.updatePositions()
        self.searchEntry.setFocus()
        
    def replace(self):
        # show replace stuff
        self.replaceLabel.show()
        self.replaceEntry.show()
        self.replaceButton.show()
        self.replaceAllButton.show()
        focus = self.replaceEntry if self.isVisible() and self.searchEntry.text() else self.searchEntry
        self._replace = True # we are in replace mode
        self.showWidget()
        self.updatePositions()
        focus.setFocus()
        
    def slotSearchChanged(self):
        self.updatePositions()
        self.currentView().setSearchResults(self._positions)

    def updatePositions(self):
        search = self.searchEntry.text()
        view = self.currentView()
        document = view.document()
        self._positions = []
        if search:
            text = document.toPlainText()
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
                    c.setPosition(m.end())
                    c.setPosition(m.start(), QTextCursor.KeepAnchor)
                    self._positions.append(c)
        self.countLabel.setText(unicode(len(self._positions)))
        
    def findNext(self):
        view = self.currentView()
        if view and self._positions:
            positions = [c.position() for c in self._positions]
            index = bisect.bisect_right(positions, view.textCursor().position())
            if index < len(positions):
                view.setTextCursor(self._positions[index])
            else:
                view.setTextCursor(self._positions[0])
            view.ensureCursorVisible()

    def findPrevious(self):
        view = self.currentView()
        positions = [c.position() for c in self._positions]
        if view and positions:
            index = bisect.bisect_left(positions, view.textCursor().position()) - 1
            view.setTextCursor(self._positions[index])
            view.ensureCursorVisible()

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Tab:
            # prevent Tab from reaching the View widget
            self.window().focusNextChild()
            return
        # if in search mode, Up and Down jump between search results
        if not self._replace and self._positions and self.searchEntry.text() and not ev.modifiers():
            if ev.key() == Qt.Key_Up:
                self.findPrevious()
                return
            elif ev.key() ==  Qt.Key_Down:
                self.findNext()
                return
        super(Search, self).keyPressEvent(ev)

    def doReplace(self, cursor):
        text = cursor.selection().toPlainText()
        search = self.searchEntry.text()
        replace = self.replaceEntry.text()
        ok = text == self.searchEntry.text()
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
        view = self.currentView()
        if view and self._positions:
            positions = [c.position() for c in self._positions]
            index = bisect.bisect_left(positions, view.textCursor().position())
            if index >= len(positions):
                index = 0
            if self.doReplace(self._positions[index]):
                view.setSearchResults(self._positions)
                if index < len(positions) - 1:
                    view.setTextCursor(self._positions[index+1])
                else:
                    view.setTextCursor(self._positions[0])
                view.ensureCursorVisible()
    
    def slotReplaceAll(self):
        view = self.currentView()
        if view:
            replaced = False
            cursors = self._positions
            if view.textCursor().hasSelection():
                cursors = [cursor for cursor in cursors if cursorContains(view.textCursor(), cursor)]
            view.textCursor().beginEditBlock()
            for cursor in cursors:
                if self.doReplace(cursor):
                    replaced = True
            view.textCursor().endEditBlock()
            if replaced:
                view.setSearchResults(self._positions)


def cursorContains(cursor1, cursor2):
    """Returns True if the selection of cursor2 entirely falls inside the selection of cursor1."""
    start1, end1 = sorted((cursor1.position(), cursor1.anchor()))
    start2, end2 = sorted((cursor2.position(), cursor2.anchor()))
    return start1 <= start2 and end1 >= end2

