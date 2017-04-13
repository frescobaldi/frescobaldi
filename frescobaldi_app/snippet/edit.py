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
The dialog for editing a snippet
"""



import re

from PyQt5.QtCore import QItemSelectionModel, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QTextCharFormat
from PyQt5.QtWidgets import (
    QAction, QDialog, QDialogButtonBox, QGridLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout)

import actioncollectionmanager
import app
import qutil
import userguide
import cursorkeys
import icons
import textformats
import wordboundary
import gadgets.indenter
import gadgets.matcher
import widgets

from . import model
from . import snippets
from . import builtin
from . import expand
from . import highlight
from . import completer


class Edit(QDialog):
    """Dialog for editing a snippet. It is used for one edit.

    Use None as the name to create a new snippet. In that case, text
    is set as a default in the text edit.

    """
    def __init__(self, widget, name, text=""):
        super(Edit, self).__init__(widget)

        self._name = name

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.topLabel = QLabel()
        self.text = QTextEdit(cursorWidth=2, acceptRichText=False)
        self.titleLabel = QLabel()
        self.titleEntry = QLineEdit()
        self.shortcutLabel = QLabel()
        self.shortcutButton = ShortcutButton(clicked=self.editShortcuts)

        layout.addWidget(self.topLabel)
        layout.addWidget(self.text)

        grid = QGridLayout()
        layout.addLayout(grid)

        grid.addWidget(self.titleLabel, 0, 0)
        grid.addWidget(self.titleEntry, 0, 1)
        grid.addWidget(self.shortcutLabel, 1, 0)
        grid.addWidget(self.shortcutButton, 1, 1)

        layout.addWidget(widgets.Separator())

        b = QDialogButtonBox(accepted=self.accept, rejected=self.reject)
        layout.addWidget(b)

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        if name and name in builtin.builtin_snippets:
            b.setStandardButtons(buttons | QDialogButtonBox.RestoreDefaults)
            b.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.slotDefaults)
        else:
            b.setStandardButtons(buttons)
        userguide.addButton(b, "snippet_editor")

        # PyQt5.10 en sip4.14.5 delete the Highlighter, even though it is
        # constructed with a parent, that's why we save it in an unused attribute.
        self._highlighter = highlight.Highlighter(self.text.document())
        Matcher(self.text)
        gadgets.indenter.Indenter(self.text)
        self.text.installEventFilter(cursorkeys.handler)
        wordboundary.handler.install_textedit(self.text)
        completer.Completer(self.text)

        if name:
            self.titleEntry.setText(snippets.title(name, False) or '')
            self.text.setPlainText(snippets.text(name))
            ac = self.parent().parent().snippetActions
            self.setShortcuts(ac.shortcuts(name))
        else:
            self.text.setPlainText(text)
            self.setShortcuts(None)

        app.translateUI(self)

        self.readSettings()
        app.settingsChanged.connect(self.readSettings)
        qutil.saveDialogSize(self, "snippettool/editor/size", QSize(400, 300))
        self.show()

    def translateUI(self):
        title = _("Edit Snippet") if self._name else _("New Snippet")
        self.setWindowTitle(app.caption(title))
        self.topLabel.setText(_("Snippet Text:"))
        self.titleLabel.setText(_("Title:"))
        self.shortcutLabel.setText(_("Shortcut:"))
        self.shortcutButton.updateText()

    def done(self, result):
        if result:
            if not self.text.toPlainText():
                QMessageBox.warning(self,
                    _("Empty Snippet"),
                    _("A snippet can't be empty."))
                return
            self.saveSnippet()
        elif self.text.document().isModified():
            res = QMessageBox.warning(self, self.windowTitle(),
                _("The snippet has been modified.\n"
                  "Do you want to save your changes or discard them?"),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if res == QMessageBox.Cancel:
                return
            elif res != QMessageBox.Discard:
                self.saveSnippet()
        super(Edit, self).done(result)

    def readSettings(self):
        data = textformats.formatData('editor')
        self.text.setFont(data.font)
        self.text.setPalette(data.palette())

    def shortcuts(self):
        return self.shortcutButton.shortcuts()

    def setShortcuts(self, shortcuts):
        self.shortcutButton.setShortcuts(shortcuts)

    def editShortcuts(self):
        from widgets import shortcuteditdialog
        ac = self.parent().parent().snippetActions
        action = QAction(None)
        if self._name:
            action.setShortcuts(self.shortcuts())
            action.setIcon(snippets.icon(self._name) or QIcon())
            default = ac.defaults().get(self._name)
            text = snippets.title(self._name)
        else:
            default = None
            text = self.titleEntry.text() or _("Untitled")
        action.setText(text.replace('&', '&&'))

        cb = self.actionManager().findShortcutConflict
        skip = (self.parent().parent().snippetActions, self._name)
        dlg = shortcuteditdialog.ShortcutEditDialog(self, cb, skip)

        if dlg.editAction(action, default):
            self.setShortcuts(action.shortcuts())

    def saveSnippet(self):
        index = model.model().saveSnippet(self._name,
            self.text.toPlainText(), self.titleEntry.text())
        # set snippet current in the editor that called us
        self.parent().treeView.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
        #remove the shortcuts conflicts
        self.actionManager().removeShortcuts(self.shortcuts())
        self.parent().treeView.update()
        # get the name that was used
        name = model.model().name(index)
        self.parent().parent().snippetActions.setShortcuts(name, self.shortcuts())
        self.text.document().setModified(False)

    def actionManager(self):
        mainwindow = self.parent().parent().mainwindow()
        return actioncollectionmanager.manager(mainwindow)

    def slotDefaults(self):
        t = builtin.builtin_snippets[self._name]
        self.text.setPlainText(t.text)
        self.titleEntry.setText(t.title() if t.title else '')
        self.setShortcuts(self.parent().parent().snippetActions.defaults().get(self._name))


class ShortcutButton(QPushButton):
    def __init__(self, **args):
        super(ShortcutButton, self).__init__(**args)
        self.setIcon(icons.get("preferences-desktop-keyboard-shortcuts"))
        self._shortcuts = []

    def shortcuts(self):
        return self._shortcuts

    def setShortcuts(self, shortcuts):
        self._shortcuts = shortcuts or []
        self.updateText()

    def updateText(self):
        if not self._shortcuts:
            self.setText(_("None"))
        else:
            key = self._shortcuts[0].toString(QKeySequence.NativeText)
            if len(self._shortcuts) > 1:
                key += "..."
            self.setText(key.replace('&', '&&'))
        self.setToolTip(_("Click to change the keyboard shortcut."))


class Matcher(gadgets.matcher.Matcher):
    def __init__(self, edit):
        super(Matcher, self).__init__(edit)
        self.readSettings()
        app.settingsChanged.connect(self.readSettings)

    def readSettings(self):
        self.format = QTextCharFormat()
        self.format.setBackground(textformats.formatData('editor').baseColors['match'])


