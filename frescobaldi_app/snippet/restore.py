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
Restored changed or deleted builtin snippets.
"""



from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem

import app
import userguide
import qutil
import widgets.dialog

from . import builtin
from . import snippets
from . import model
from . import widget


class RestoreDialog(widgets.dialog.Dialog):
    def __init__(self, parent=None):
        super(RestoreDialog, self).__init__(parent)
        self.messageLabel().setWordWrap(True)
        userguide.addButton(self.buttonBox(), "snippets")
        self.tree = QTreeWidget(headerHidden=True, rootIsDecorated=False)
        self.setMainWidget(self.tree)

        self.deletedItem = QTreeWidgetItem(self.tree)
        self.deletedItem.setFlags(Qt.ItemIsUserCheckable)
        self.changedItem = QTreeWidgetItem(self.tree)
        self.changedItem.setFlags(Qt.ItemIsUserCheckable)
        self.tree.itemChanged.connect(self.slotItemChanged)

        app.translateUI(self)
        app.languageChanged.connect(self.populate)
        self.accepted.connect(self.updateSnippets)
        qutil.saveDialogSize(self, "snippettool/restoredialog/size")

    def translateUI(self):
        self.setWindowTitle(
            app.caption(_("dialog title", "Restore Built-in Snippets")))
        self.setMessage(_(
            "This dialog allows you to recover built-in snippets that have "
            "been changed or deleted. Check the snippets you want to recover "
            "and click the button \"Restore Checked Snippets.\""))
        self.button("ok").setText(_("Restore Checked Snippets"))
        self.deletedItem.setText(0, _("Deleted Snippets"))
        self.changedItem.setText(0, _("Changed Snippets"))

    def populate(self):
        """Puts the deleted/changed snippets in the tree."""
        self.deletedItem.takeChildren()
        self.deletedItem.setExpanded(True)
        self.deletedItem.setCheckState(0, Qt.Unchecked)
        self.changedItem.takeChildren()
        self.changedItem.setExpanded(True)
        self.changedItem.setCheckState(0, Qt.Unchecked)

        builtins = list(builtin.builtin_snippets)
        builtins.sort(key = snippets.title)

        names = frozenset(snippets.names())

        for name in builtins:
            if name in names:
                if snippets.isoriginal(name):
                    continue
                parent = self.changedItem
            else:
                parent = self.deletedItem

            item = QTreeWidgetItem(parent)
            item.name = name
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(0, Qt.Unchecked)
            item.setText(0, snippets.title(name))

        self.deletedItem.setDisabled(self.deletedItem.childCount() == 0)
        self.changedItem.setDisabled(self.changedItem.childCount() == 0)
        self.checkOkButton()

    def slotItemChanged(self, item):
        if item in (self.deletedItem, self.changedItem):
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, item.checkState(0))
        self.checkOkButton()

    def checkedSnippets(self):
        """Yields the names of the checked snippets."""
        for parent in (self.deletedItem, self.changedItem):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.checkState(0) == Qt.Checked:
                    yield child.name

    def updateSnippets(self):
        """Restores the checked snippets."""
        collection = self.parent().parent().snippetActions
        for name in self.checkedSnippets():
            collection.restoreDefaultShortcuts(name)
            model.model().saveSnippet(name, None, None)

    def checkOkButton(self):
        """Enables the OK button if there are selected snippets."""
        self.button("ok").setEnabled(any(self.checkedSnippets()))


