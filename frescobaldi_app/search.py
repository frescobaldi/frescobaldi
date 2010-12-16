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
        
        app.translateUI(self)
        
    def translateUI(self):
        self.searchLabel.setText(_("Search:"))
        self.caseCheck.setText(_("&Case"))
        self.caseCheck.setToolTip(_("Case Sensitive"))
        self.regexCheck.setText(_("&Regex"))
        self.regexCheck.setToolTip(_("Regular Expression"))
        self.countLabel.setToolTip(_("The total number of matches"))
        
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
        # TODO: hide replace stuff
        if not self.isVisible():
            with util.signalsBlocked(self.searchEntry):
                self.searchEntry.clear()
            self.showWidget()
        self.searchEntry.setFocus()
        
    def replace(self):
        # TODO: show replace stuff

        self.showWidget()
        
    def slotSearchChanged(self):
        self.searchEntry.setFocus()
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
        positions = [c.position() for c in self._positions]
        if view and positions:
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
        if self._positions and self.searchEntry.text() and not ev.modifiers():
            if ev.key() == Qt.Key_Up:
                self.findPrevious()
                return
            elif ev.key() ==  Qt.Key_Down:
                self.findNext()
                return
        super(Search, self).keyPressEvent(ev)






