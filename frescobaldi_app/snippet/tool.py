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
The snippets dockwindow.
"""


import weakref

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import app
import panel


class SnippetTool(panel.Panel):
    """A dockwidget for selecting, applying and editing the list of snippets."""
    def __init__(self, mainwindow):
        super(SnippetTool, self).__init__(mainwindow)
        self.hide()
        self.snippetActions = SnippetActions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(self.snippetActions)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+S"))
        ac = self.actionCollection = Actions()
        mainwindow.addAction(ac.snippettool_activate)
        ac.snippettool_activate.triggered.connect(self.activate)
        ac.file_save_as_template.triggered.connect(self.saveAsTemplate)
        ac.copy_to_snippet.triggered.connect(self.copyToSnippet)
        ac.templates_manage.triggered.connect(self.manageTemplates)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        mainwindow.addDockWidget(Qt.BottomDockWidgetArea, self)
        mainwindow.selectionStateChanged.connect(self.updateActions)
        self.updateActions()

    def translateUI(self):
        self.setWindowTitle(_("Snippets"))
        self.toggleViewAction().setText(_("&Snippets"))

    def createWidget(self):
        from . import widget
        return widget.Widget(self)

    def activate(self):
        super(SnippetTool, self).activate()
        if self.isFloating():
            self.activateWindow()
        self.mainwindow().currentView().ensureCursorVisible()
        self.widget().searchEntry.setFocus()
        self.widget().searchEntry.selectAll()

    def updateActions(self):
        self.actionCollection.copy_to_snippet.setEnabled(self.mainwindow().hasSelection())

    def saveAsTemplate(self):
        from . import template
        template.save(self.mainwindow())

    def copyToSnippet(self):
        text = self.mainwindow().textCursor().selection().toPlainText()
        text = '-*- menu;\n' + text
        from . import edit
        edit.Edit(self.widget(), None, text)

    def manageTemplates(self):
        super(SnippetTool, self).activate()
        if self.isFloating():
            self.activateWindow()
        self.widget().searchEntry.setText(":template")


class Actions(actioncollection.ActionCollection):
    name = "snippettool"
    def createActions(self, parent=None):
        self.file_save_as_template = QAction(parent)
        self.copy_to_snippet = QAction(parent)
        self.templates_manage = QAction(parent)
        self.snippettool_activate = QAction(parent)
        self.snippettool_activate.setShortcut(QKeySequence("Ctrl+T"))

    def translateUI(self):
        self.file_save_as_template.setText(_("Save as Template..."))
        self.copy_to_snippet.setText(_("Copy to &Snippet..."))
        self.templates_manage.setText(_("Manage Templates..."))
        self.snippettool_activate.setText(_("Manage &Snippets..."))


class SnippetActions(actioncollection.ShortcutCollection):
    """Manages keyboard shortcuts for the snippets."""
    name = "snippets"
    def __init__(self, tool):
        super(SnippetActions, self).__init__(tool.mainwindow().centralWidget())
        self.tool = weakref.ref(tool)

    def createDefaultShortcuts(self):
        self.setDefaultShortcuts('voice1', [QKeySequence('Alt+1')])
        self.setDefaultShortcuts('voice2', [QKeySequence('Alt+2')])
        self.setDefaultShortcuts('voice3', [QKeySequence('Alt+3')])
        self.setDefaultShortcuts('voice4', [QKeySequence('Alt+4')])
        self.setDefaultShortcuts('1voice', [QKeySequence('Alt+0')])
        self.setDefaultShortcuts('times23', [QKeySequence('Ctrl+3')])
        self.setDefaultShortcuts('ly_version', [QKeySequence('Ctrl+Shift+V')])
        self.setDefaultShortcuts('blankline', [QKeySequence('Ctrl+Shift+Return')])
        self.setDefaultShortcuts('next_blank_line', [QKeySequence('Alt+Down')])
        self.setDefaultShortcuts('previous_blank_line', [QKeySequence('Alt+Up')])
        self.setDefaultShortcuts('next_blank_line_select', [QKeySequence('Alt+Shift+Down')])
        self.setDefaultShortcuts('previous_blank_line_select', [QKeySequence('Alt+Shift+Up')])
        self.setDefaultShortcuts('removelines', [QKeySequence('Ctrl+K')])
        self.setDefaultShortcuts('repeat', [QKeySequence('Ctrl+Shift+R')])
        self.setDefaultShortcuts('quotes_s', [QKeySequence("Ctrl+'")])
        self.setDefaultShortcuts('quotes_d', [QKeySequence('Ctrl+"')])
        self.setDefaultShortcuts('uppercase', [QKeySequence('Ctrl+U')])
        self.setDefaultShortcuts('lowercase', [QKeySequence('Ctrl+Shift+U')])
        self.setDefaultShortcuts('last_note', [QKeySequence('Ctrl+;')])
        self.setDefaultShortcuts('double', [QKeySequence('Ctrl+D')])
        self.setDefaultShortcuts('comment', [QKeySequence('Ctrl+Alt+C, Ctrl+Alt+C')])
        self.setDefaultShortcuts('uncomment', [QKeySequence('Ctrl+Alt+C, Ctrl+Alt+U')])

    def realAction(self, name):
        from . import actions, model
        if name in model.model().names():
            return actions.action(name, None, self)

    def triggerAction(self, name):
        from . import insert, model
        if name in model.model().names():
            view = self.tool().mainwindow().currentView()
            if view.hasFocus() or self.tool().widget().searchEntry.hasFocus():
                insert.insert(name, view)

    def title(self):
        return _("Snippets")


