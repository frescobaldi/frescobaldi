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
Place snippets in menu.

If a snippet defines the variable 'menu' it is placed in the menu, sorted
on its internal action name and grouped by the value of the 'menu' variable.

If a snippet defines the variable 'template' it is placed in File->New from
template, sorted on its action name and grouped by the value of the 'template'
variable.

TODO:
- provide submenus
- caching (keep actions alive?)

"""


from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QMenu

import app
import document
import qutil
import panelmanager


class SnippetMenuBase(QMenu):
    def __init__(self, parent=None):
        super(SnippetMenuBase, self).__init__(parent)
        self.aboutToShow.connect(self.populate)
        self.aboutToHide.connect(self.clearMenu, Qt.QueuedConnection)
        self.triggered.connect(self.slotTriggered)
        app.translateUI(self)

    def mainwindow(self):
        return self.parent().window()

    def tool(self):
        """Returns the snippets tool."""
        return panelmanager.manager(self.mainwindow()).snippettool

    def populate(self):
        """Populates the menu with snippet actions."""
        self.clearMenu() # on some systems aboutToHide does not fire...
        from . import model, snippets, actions
        last = self.insertBeforeAction()
        shortcuts = self.tool().snippetActions
        groups = {}
        for name in sorted(model.model().names()):
            variables = snippets.get(name).variables
            group = self.snippetGroup(variables)
            if group:
                action = actions.action(name, self.mainwindow(), shortcuts)
                self.visitAction(action, variables)
                groups.setdefault(group, []).append(action)
        for group in sorted(groups, key=lambda g: '' if g is True else g):
            for action in groups[group]:
                self.insertAction(last, action)
            self.insertSeparator(last)
        qutil.addAccelerators(self.actions())

    def insertBeforeAction(self):
        """Should return an action to insert out stuff before, or None."""
        return None

    def snippetGroup(self, variables):
        """Should a group name if the snippet is to appear in the menu."""

    def visitAction(self, action, variables):
        """May change the action depending on variables."""

    def clearMenu(self):
        """Should delete the inserted actions."""
        for a in self.actions():
            self.removeAction(a)
            a.deleteLater()

    def slotTriggered(self, action):
        """Called when an action is triggered."""
        name = action.objectName()
        if name:
            self.applySnippet(name)

    def applySnippet(self, name):
        """Applies the named snippet."""
        from . import insert
        view = self.mainwindow().currentView()
        view.setFocus()
        insert.insert(name, view)


class SnippetMenu(SnippetMenuBase):
    def __init__(self, parent=None):
        super(SnippetMenu, self).__init__(parent)
        self.addAction(self.tool().actionCollection.snippettool_activate)

    def translateUI(self):
        self.setTitle(_("menu title", "Sn&ippets"))

    def insertBeforeAction(self):
        return self.actions()[-1]

    def snippetGroup(self, variables):
        return variables.get('menu')

    def visitAction(self, action, variables):
        if 'yes' in variables.get('selection', ''):
            action.setEnabled(self.mainwindow().hasSelection())

    def clearMenu(self):
        """Deletes the actions on menu hide, excepts the "Snippets..." action."""
        for a in self.actions()[:-1]:
            self.removeAction(a)
            a.deleteLater()


class TemplateMenu(SnippetMenuBase):
    def __init__(self, parent=None):
        super(TemplateMenu, self).__init__(parent)
        self.addAction(self.tool().actionCollection.templates_manage)

    def translateUI(self):
        self.setTitle(_("New from &Template"))

    def insertBeforeAction(self):
        return self.actions()[-1]

    def snippetGroup(self, variables):
        return variables.get('template')

    def applySnippet(self, name):
        d = app.openUrl(QUrl())
        self.mainwindow().setCurrentDocument(d)
        super(TemplateMenu, self).applySnippet(name)
        d.setUndoRedoEnabled(False)
        d.setUndoRedoEnabled(True) # d.clearUndoRedoStacks() only in Qt >= 4.7
        d.setModified(False)
        from . import snippets
        if 'template-run' in snippets.get(name).variables:
            import engrave
            engrave.engraver(self.mainwindow()).engrave('preview', d)

    def clearMenu(self):
        """Deletes the actions on menu hide, except "Manage templates..."."""
        for a in self.actions()[:-1]:
            self.removeAction(a)
            a.deleteLater()


