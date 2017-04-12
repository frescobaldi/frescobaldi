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
The snippets widget.
"""


from PyQt5.QtCore import QEvent, QItemSelectionModel, QModelIndex, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction, QApplication, QCompleter, QFileDialog, QHBoxLayout, QMenu,
    QMessageBox, QPushButton, QSplitter, QTextBrowser, QToolButton,
    QTreeView, QVBoxLayout, QWidget)

import app
import userguide
import icons
import widgets.lineedit
import textformats
import actioncollectionmanager

from . import actions
from . import model
from . import snippets
from . import edit
from . import insert
from . import highlight


class Widget(QWidget):
    def __init__(self, panel):
        super(Widget, self).__init__(panel)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)

        self.searchEntry = SearchLineEdit()
        self.treeView = QTreeView(contextMenuPolicy=Qt.CustomContextMenu)
        self.textView = QTextBrowser()

        applyButton = QToolButton(autoRaise=True)
        editButton = QToolButton(autoRaise=True)
        addButton = QToolButton(autoRaise=True)
        self.menuButton = QPushButton(flat=True)
        menu = QMenu(self.menuButton)
        self.menuButton.setMenu(menu)

        splitter = QSplitter(Qt.Vertical)
        top = QHBoxLayout()
        layout.addLayout(top)
        splitter.addWidget(self.treeView)
        splitter.addWidget(self.textView)
        layout.addWidget(splitter)
        splitter.setSizes([200, 100])
        splitter.setCollapsible(0, False)

        top.addWidget(self.searchEntry)
        top.addWidget(applyButton)
        top.addSpacing(10)
        top.addWidget(addButton)
        top.addWidget(editButton)
        top.addWidget(self.menuButton)

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

        # import action
        a = self.importAction = act(self.slotImport, 'document-open')
        menu.addAction(a)

        # export action
        a = self.exportAction = act(self.slotExport, 'document-save-as')
        menu.addAction(a)

        # apply button
        a = self.applyAction = act(self.slotApply, 'edit-paste')
        applyButton.setDefaultAction(a)
        menu.addSeparator()
        menu.addAction(a)

        # add button
        a = self.addAction_ = act(self.slotAdd, 'list-add')
        a.setShortcut(QKeySequence(Qt.Key_Insert))
        addButton.setDefaultAction(a)
        menu.addSeparator()
        menu.addAction(a)

        # edit button
        a = self.editAction = act(self.slotEdit, 'document-edit')
        a.setShortcut(QKeySequence(Qt.Key_F2))
        editButton.setDefaultAction(a)
        menu.addAction(a)

        # set shortcut action
        a = self.shortcutAction = act(self.slotShortcut, 'preferences-desktop-keyboard-shortcuts')
        menu.addAction(a)

        # delete action
        a = self.deleteAction = act(self.slotDelete, 'list-remove')
        a.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Delete))
        menu.addAction(a)

        # restore action
        a = self.restoreAction = act(self.slotRestore)
        menu.addSeparator()
        menu.addAction(a)

        # help button
        a = self.helpAction = act(self.slotHelp, 'help-contents')
        menu.addSeparator()
        menu.addAction(a)

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
        self.treeView.customContextMenuRequested.connect(self.showContextMenu)
        self.treeView.selectionModel().currentChanged.connect(self.updateText)
        self.treeView.model().dataChanged.connect(self.updateFilter)

        # highlight text
        self.highlighter = highlight.Highlighter(self.textView.document())

        # complete on snippet variables
        self.searchEntry.setCompleter(QCompleter([
            ':icon', ':indent', ':menu', ':name', ':python', ':selection',
            ':set', ':symbol', ':template', ':template-run'], self.searchEntry))
        self.readSettings()
        app.settingsChanged.connect(self.readSettings)
        app.translateUI(self)
        self.updateColumnSizes()
        self.setAcceptDrops(True)

    def dropEvent(self, ev):
        if not ev.source() and ev.mimeData().hasUrls():
            filename = ev.mimeData().urls()[0].toLocalFile()
            if filename:
                ev.accept()
                from . import import_export
                import_export.load(filename, self)

    def dragEnterEvent(self, ev):
        if not ev.source() and ev.mimeData().hasUrls():
            ev.accept()

    def translateUI(self):
        try:
            self.searchEntry.setPlaceholderText(_("Search..."))
        except AttributeError:
            pass # not in Qt 4.6
        shortcut = lambda a: a.shortcut().toString(QKeySequence.NativeText)
        self.menuButton.setText(_("&Menu"))
        self.addAction_.setText(_("&Add..."))
        self.addAction_.setToolTip(
            _("Add a new snippet. ({key})").format(key=shortcut(self.addAction_)))
        self.editAction.setText(_("&Edit..."))
        self.editAction.setToolTip(
            _("Edit the current snippet. ({key})").format(key=shortcut(self.editAction)))
        self.shortcutAction.setText(_("Configure Keyboard &Shortcut..."))
        self.deleteAction.setText(_("&Remove"))
        self.deleteAction.setToolTip(_("Remove the selected snippets."))
        self.applyAction.setText(_("A&pply"))
        self.applyAction.setToolTip(_("Apply the current snippet."))
        self.importAction.setText(_("&Import..."))
        self.importAction.setToolTip(_("Import snippets from a file."))
        self.exportAction.setText(_("E&xport..."))
        self.exportAction.setToolTip(_("Export snippets to a file."))
        self.restoreAction.setText(_("Restore &Built-in Snippets..."))
        self.restoreAction.setToolTip(
            _("Restore deleted or changed built-in snippets."))
        self.helpAction.setText(_("&Help"))
        self.searchEntry.setToolTip(_(
            "Enter text to search in the snippets list.\n"
            "See \"What's This\" for more information."))
        self.searchEntry.setWhatsThis(''.join(map("<p>{0}</p>\n".format, (
            _("Enter text to search in the snippets list, and "
              "press Enter to apply the currently selected snippet."),
            _("If the search text fully matches the value of the '{name}' variable "
              "of a snippet, that snippet is selected.").format(name="name"),
            _("If the search text starts with a colon ':', the rest of the "
              "search text filters snippets that define the given variable. "
              "After a space a value can also be entered, snippets will then "
              "match if the value of the given variable contains the text after "
              "the space."),
            _("E.g. entering {menu} will show all snippets that are displayed "
              "in the insert menu.").format(menu="<code>:menu</code>"),
            ))))

    def sizeHint(self):
        return self.parent().mainwindow().size() / 4

    def readSettings(self):
        data = textformats.formatData('editor')
        self.textView.setFont(data.font)
        self.textView.setPalette(data.palette())

    def showContextMenu(self, pos):
        """Called when the user right-clicks the tree view."""
        self.menuButton.menu().popup(self.treeView.viewport().mapToGlobal(pos))

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
        view = self.parent().mainwindow().currentView()
        insert.insert(name, view)

    def slotAdd(self):
        """Called when the user wants to add a new snippet."""
        edit.Edit(self, None)

    def slotEdit(self):
        """Called when the user wants to edit a snippet."""
        name = self.currentSnippet()
        if name:
            edit.Edit(self, name)

    def slotShortcut(self):
        """Called when the user selects the Configure Shortcut action."""
        from widgets import shortcuteditdialog
        name = self.currentSnippet()
        if name:
            collection = self.parent().snippetActions
            action = actions.action(name, None, collection)
            default = collection.defaults().get(name)
            mgr = actioncollectionmanager.manager(self.parent().mainwindow())
            cb = mgr.findShortcutConflict
            dlg = shortcuteditdialog.ShortcutEditDialog(self, cb, (collection, name))

            if dlg.editAction(action, default):
                mgr.removeShortcuts(action.shortcuts())
                collection.setShortcuts(name, action.shortcuts())
                self.treeView.update()

    def slotDelete(self):
        """Called when the user wants to delete the selected rows."""
        rows = sorted(set(i.row() for i in self.treeView.selectedIndexes()), reverse=True)
        if rows:
            for row in rows:
                name = self.treeView.model().names()[row]
                self.parent().snippetActions.setShortcuts(name, [])
                self.treeView.model().removeRow(row)
            self.updateFilter()

    def slotApply(self):
        """Called when the user clicks the apply button. Applies current snippet."""
        name = self.currentSnippet()
        if name:
            view = self.parent().mainwindow().currentView()
            insert.insert(name, view)

    def slotImport(self):
        """Called when the user activates the import action."""
        filetypes = "{0} (*.xml);;{1} (*)".format(_("XML Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import Snippets"))
        filename = None
        filename = QFileDialog.getOpenFileName(self, caption, filename, filetypes)[0]
        if filename:
            from . import import_export
            import_export.load(filename, self)

    def slotExport(self):
        """Called when the user activates the export action."""
        allrows = [row for row in range(model.model().rowCount())
                       if not self.treeView.isRowHidden(row, QModelIndex())]
        selectedrows = [i.row() for i in self.treeView.selectedIndexes()
                                if i.column() == 0 and i.row() in allrows]
        names = self.treeView.model().names()
        names = [names[row] for row in selectedrows or allrows]

        filetypes = "{0} (*.xml);;{1} (*)".format(_("XML Files"), _("All Files"))
        n = len(names)
        caption = app.caption(_("dialog title",
            "Export {num} Snippet", "Export {num} Snippets", n).format(num=n))
        filename = QFileDialog.getSaveFileName(self, caption, None, filetypes)[0]
        if filename:
            from . import import_export
            try:
                import_export.save(names, filename)
            except (IOError, OSError) as e:
                QMessageBox.critical(self, _("Error"), _(
                    "Can't write to destination:\n\n{url}\n\n{error}").format(
                    url=filename, error=e.strerror))

    def slotRestore(self):
        """Called when the user activates the Restore action."""
        from . import restore
        dlg = restore.RestoreDialog(self)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.populate()
        dlg.show()
        dlg.finished.connect(dlg.deleteLater)

    def slotHelp(self):
        """Called when the user clicks the small help button."""
        userguide.show("snippets")

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
        self.textView.clear()
        if name:
            s = snippets.get(name)
            self.highlighter.setPython('python' in s.variables)
            self.textView.setPlainText(s.text)

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


