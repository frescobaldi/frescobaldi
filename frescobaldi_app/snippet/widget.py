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
The snippets widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons
import widgets.lineedit
import textformats

from . import actions
from . import model
from . import snippets

class Widget(QWidget):
    def __init__(self, panel):
        super(Widget, self).__init__(panel)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        
        self.searchEntry = SearchLineEdit()
        self.treeView = QTreeView()
        self.infoLine = QLabel()
        self.textView = QTextBrowser()
        
        self.addButton = QToolButton(autoRaise=True, icon=icons.get('list-add'))
        self.editButton = QToolButton(autoRaise=True, icon=icons.get('preferences-system'))
        self.removeButton = QToolButton(autoRaise=True, icon=icons.get('list-remove'))
        self.applyButton = QToolButton(autoRaise=True, icon=icons.get('edit-paste'))
        
        top = QHBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.treeView)
        layout.addWidget(self.infoLine)
        layout.addWidget(self.textView)
        
        top.addWidget(self.searchEntry)
        top.addSpacing(10)
        top.addWidget(self.addButton)
        top.addWidget(self.editButton)
        top.addWidget(self.removeButton)
        top.addSpacing(10)
        top.addWidget(self.applyButton)
        
        # hide if ESC pressed in lineedit
        a = QAction(self.searchEntry)
        self.searchEntry.addAction(a)
        a.setShortcut(QKeySequence(Qt.Key_Escape))
        a.setShortcutContext(Qt.WidgetShortcut)
        a.triggered.connect(self.slotEscapePressed)
        
        self.treeView.setSelectionBehavior(QTreeView.SelectRows)
        self.treeView.setSelectionMode(QTreeView.ExtendedSelection)
        self.treeView.setRootIsDecorated(False)
        self.treeView.setAllColumnsShowFocus(True)
        self.treeView.setModel(model.model())
        
        # signals
        self.searchEntry.returnPressed.connect(self.slotReturnPressed)
        self.searchEntry.textChanged.connect(self.updateFilter)
        self.removeButton.clicked.connect(self.slotDelete)
        self.applyButton.clicked.connect(self.slotApply)
        self.treeView.selectionModel().currentChanged.connect(self.updateText)
        
        self.setInfoText('')
        self.readSettings()
        app.settingsChanged.connect(self.readSettings)
        app.translateUI(self)
        self.updateColumnSizes()

    def translateUI(self):
        try:
            self.searchEntry.setPlaceHolderText(_("Search..."))
        except AttributeError:
            pass # not in Qt 4.6
    
    def sizeHint(self):
        return self.parent().mainwindow().size() / 4
        
    def setInfoText(self, text):
        if text:
            self.infoLine.setText(text)
        self.infoLine.setVisible(bool(text))
        
    def readSettings(self):
        data = textformats.formatData('editor')
        self.textView.setFont(data.font)
        self.textView.setPalette(data.palette())

    def slotReturnPressed(self):
        """Called when the user presses Return in the search entry. Applies current snippet."""
        name = self.currentSnippet()
        if name:
            view = self.parent().mainwindow().currentView()
            actions.applySnippet(view, name)
            self.parent().hide() # make configurable?
            view.setFocus()

    def slotEscapePressed(self):
        """Called when the user presses ESC in the search entry. Hides the panel."""
        self.parent().hide()
        self.parent().mainwindow().currentView().setFocus()

    def slotDelete(self):
        """Called when the user wants to delete the selected rows."""
        rows = sorted(set(i.row() for i in self.treeView.selectedIndexes()), reverse=True)
        for row in rows:
            self.treeView.model().removeRow(row)
        self.updateColumnSizes()
        self.updateFilter()
    
    def slotApply(self):
        """Called when the user clicks the apply button. Applies current snippet."""
        name = self.currentSnippet()
        if name:
            view = self.parent().mainwindow().currentView()
            actions.applySnippet(view, name)
        
    def currentSnippet(self):
        """Returns the name of the current snippet if it is visible."""
        row = self.treeView.currentIndex().row()
        if row != -1 and not self.treeView.isRowHidden(row, QModelIndex()):
            return self.treeView.model().names()[row]

    def updateFilter(self):
        """Called when the text in the entry changes, updates search results."""
        text = self.searchEntry.text()
        ltext = text.lower()
        for row in range(self.treeView.model().rowCount()):
            name = self.treeView.model().names()[row]
            hide = False
            if snippets.get(name)[1].get('name') == text:
                i = self.treeView.model().createIndex(row, 0)
                self.treeView.selectionModel().setCurrentIndex(i, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
            elif ltext not in snippets.title(name).lower():
                hide = True
            self.treeView.setRowHidden(row, QModelIndex(), hide)
        self.updateText()
            
    def updateText(self):
        """Called when the current snippet changes."""
        name = self.currentSnippet()
        text = snippets.get(name)[0] if name else ''
        self.textView.setText(text)
        
    def updateColumnSizes(self):
        self.treeView.resizeColumnToContents(0)
        self.treeView.resizeColumnToContents(1)
        

class SearchLineEdit(widgets.lineedit.LineEdit):
    def __init__(self, *args):
        super(SearchLineEdit, self).__init__(*args)
    
    def event(self, ev):
        if ev.type() == QEvent.KeyPress and any(ev.matches(key) for key in (
            QKeySequence.MoveToNextLine, QKeySequence.SelectNextLine,
            QKeySequence.MoveToPreviousLine, QKeySequence.SelectPreviousLine,
            QKeySequence.MoveToNextPage, QKeySequence.SelectNextPage,
            QKeySequence.MoveToPreviousPage, QKeySequence.SelectPreviousPage)):
            QApplication.sendEvent(self.parent().treeView, ev)
            return True
        return super(SearchLineEdit, self).event(ev)


