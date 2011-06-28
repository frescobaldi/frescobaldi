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

from . import model
from . import snippets
from . import edit
from . import insert


class Widget(QWidget):
    def __init__(self, panel):
        super(Widget, self).__init__(panel)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        
        self.searchEntry = SearchLineEdit()
        self.treeView = QTreeView()
        self.textView = QTextBrowser()
        
        addButton = QToolButton(autoRaise=True)
        editButton = QToolButton(autoRaise=True)
        removeButton = QToolButton(autoRaise=True)
        applyButton = QToolButton(autoRaise=True)
        
        splitter = QSplitter(Qt.Vertical)
        top = QHBoxLayout()
        layout.addLayout(top)
        splitter.addWidget(self.treeView)
        splitter.addWidget(self.textView)
        layout.addWidget(splitter)
        splitter.setSizes([200, 100])
        
        top.addWidget(self.searchEntry)
        top.addSpacing(10)
        top.addWidget(addButton)
        top.addWidget(editButton)
        top.addWidget(removeButton)
        top.addSpacing(10)
        top.addWidget(applyButton)
        
        # action generator for actions added to search entry
        def act(slot, icon=None):
            a = QAction(self, triggered=slot)
            self.addAction(a)
            a.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            icon and a.setIcon(icons.get(icon))
            return a
        
        # hide if ESC pressed in lineedit
        a = act(self.slotEscapePressed)
        a.setShortcut(QKeySequence(Qt.Key_Escape))
        
        # add button
        a = self.addAction_ = act(self.slotAdd, 'list-add')
        a.setShortcut(QKeySequence(Qt.Key_Insert))
        addButton.setDefaultAction(a)
        
        # edit button
        a = self.editAction = act(self.slotEdit, 'document-edit')
        a.setShortcut(QKeySequence(Qt.Key_F2))
        editButton.setDefaultAction(a)
        
        # delete button
        a = self.deleteAction = act(self.slotDelete, 'list-remove')
        a.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Delete))
        removeButton.setDefaultAction(a)
        
        # apply button
        a = self.applyAction = act(self.slotApply, 'edit-paste')
        applyButton.setDefaultAction(a)
        
        self.treeView.setSelectionBehavior(QTreeView.SelectRows)
        self.treeView.setSelectionMode(QTreeView.ExtendedSelection)
        self.treeView.setRootIsDecorated(False)
        self.treeView.setAllColumnsShowFocus(True)
        self.treeView.setModel(model.model())
        self.treeView.setCurrentIndex(QModelIndex())
        
        # signals
        self.searchEntry.returnPressed.connect(self.slotReturnPressed)
        self.searchEntry.textChanged.connect(self.updateFilter)
        self.treeView.doubleClicked.connect(self.slotDoubleClicked)
        self.treeView.selectionModel().currentChanged.connect(self.updateText)
        self.treeView.model().dataChanged.connect(self.updateFilter)
        
        self.readSettings()
        app.settingsChanged.connect(self.readSettings)
        app.translateUI(self)
        self.updateColumnSizes()

    def translateUI(self):
        try:
            self.searchEntry.setPlaceHolderText(_("Search..."))
        except AttributeError:
            pass # not in Qt 4.6
        self.addAction_.setText(_("Add..."))
        self.editAction.setText(_("Edit..."))
        self.deleteAction.setText(_("Remove"))
        self.applyAction.setText(_("Apply"))
        self.searchEntry.setToolTip(_(
            "Enter text to search in the snippets list.\n"
            "See \"What's This\" for more information."))
        self.searchEntry.setWhatsThis("<p>{0}</p><p>{1}</p><p>{2}</p>".format(
            _("If the search text fully matches the value of the '{name}' variable "
              "of a snippet, that snippet is selected.").format(name="name"),
            _("If the search text starts with a colon ':', the rest of the "
              "search text filters snippets that define the given variable. "
              "After a space a value can also be entered, snippets will then "
              "match if the value of the given variable contains the text after "
              "the space."),
            _("E.g. entering {menu} will show all snippets that are displayed "
              "in the insert menu.").format(menu="<code>:menu</code>")))
    
    def sizeHint(self):
        return self.parent().mainwindow().size() / 4
        
    def readSettings(self):
        data = textformats.formatData('editor')
        self.textView.setFont(data.font)
        self.textView.setPalette(data.palette())

    def slotReturnPressed(self):
        """Called when the user presses Return in the search entry. Applies current snippet."""
        name = self.currentSnippet()
        if name:
            view = self.parent().mainwindow().currentView()
            insert.insert(name, view)
            self.parent().hide() # make configurable?
            view.setFocus()

    def slotEscapePressed(self):
        """Called when the user presses ESC in the search entry. Hides the panel."""
        self.parent().hide()
        self.parent().mainwindow().currentView().setFocus()
    
    def slotDoubleClicked(self, index):
        name = self.treeView.model().name(index)
        edit.Edit(self, name)

    def slotAdd(self):
        """Called when the user wants to add a new snippet."""
        edit.Edit(self, None)
        
    def slotEdit(self):
        """Called when the user wants to edit a snippet."""
        name = self.currentSnippet()
        if name:
            edit.Edit(self, name)
        
    def slotDelete(self):
        """Called when the user wants to delete the selected rows."""
        rows = sorted(set(i.row() for i in self.treeView.selectedIndexes()), reverse=True)
        for row in rows:
            self.parent().snippetActions.setShortcuts(self.treeView.model().names()[row], [])
            self.treeView.model().removeRow(row)
        self.updateFilter()
    
    def slotApply(self):
        """Called when the user clicks the apply button. Applies current snippet."""
        name = self.currentSnippet()
        if name:
            view = self.parent().mainwindow().currentView()
            insert.insert(name, view)
        
    def currentSnippet(self):
        """Returns the name of the current snippet if it is visible."""
        row = self.treeView.currentIndex().row()
        if row != -1 and not self.treeView.isRowHidden(row, QModelIndex()):
            return self.treeView.model().names()[row]

    def updateFilter(self):
        """Called when the text in the entry changes, updates search results."""
        text = self.searchEntry.text()
        ltext = text.lower()
        filterVars = text.startswith(':')
        if filterVars:
            try:
                fvar, fval = text[1:].split(None, 1)
                fhide = lambda v: v.get(fvar) in (True, None) or fval not in v.get(fvar)
            except ValueError:
                fvar = text[1:].strip()
                fhide = lambda v: not v.get(fvar)
        for row in range(self.treeView.model().rowCount()):
            name = self.treeView.model().names()[row]
            nameid = snippets.get(name).variables.get('name', '')
            if filterVars:
                hide = fhide(snippets.get(name).variables)
            elif nameid == text:
                i = self.treeView.model().createIndex(row, 0)
                self.treeView.selectionModel().setCurrentIndex(i, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
                hide = False
            elif nameid.lower().startswith(ltext):
                hide = False
            elif ltext in snippets.title(name).lower():
                hide = False
            else:
                hide = True
            self.treeView.setRowHidden(row, QModelIndex(), hide)
        self.updateText()
            
    def updateText(self):
        """Called when the current snippet changes."""
        name = self.currentSnippet()
        text = snippets.get(name).text if name else ''
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


