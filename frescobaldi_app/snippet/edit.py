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
The dialog for editing a snippet
"""


from __future__ import unicode_literals

import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import actioncollectionmanager
import app
import util
import help
import icons
import textformats
import widgets.indenter
import widgets.matcher

from . import model
from . import snippets
from . import builtin
from . import expand
from . import highlight


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
        self.text = QTextEdit(cursorWidth=2)
        self.titleLabel = QLabel()
        self.titleEntry = QLineEdit()
        self.shortcutLabel = QLabel()
        self.shortcutButton = QPushButton(icon=icons.get("configure-shortcuts"),
            clicked=self.editShortcuts)
        
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
        
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Help
        if name and name in builtin.builtin_snippets:
            b.setStandardButtons(buttons | QDialogButtonBox.RestoreDefaults)
            b.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.slotDefaults)
        else:
            b.setStandardButtons(buttons)
        b.helpRequested.connect(lambda: help.help(snippet_help))
        
        highlight.Highlighter(self.text.document())
        Matcher(self.text)
        widgets.indenter.Indenter(self.text)
        
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
        util.saveDialogSize(self, "snippettool/editor/size", QSize(400, 300))
        self.show()
        
    def translateUI(self):
        title = _("Edit Snippet") if self._name else _("New Snippet")
        self.setWindowTitle(app.caption(title))
        self.topLabel.setText(_("Snippet Text:"))
        self.titleLabel.setText(_("Title:"))
        self.shortcutLabel.setText(_("Shortcut:"))
        self.updateShortcutText()
    
    def updateShortcutText(self):
        if not self._shortcuts:
            self.shortcutButton.setText(_("None"))
        else:
            key = self._shortcuts[0].toString(QKeySequence.NativeText)
            if len(self._shortcuts) > 1:
                key += "..."
            self.shortcutButton.setText(key.replace('&', '&&'))
        self.shortcutButton.setToolTip(_("Click to change the keyboard shortcut."))

    def done(self, result):
        if result:
            if not self.text.toPlainText():
                QMessageBox.warning(self, _("Empty Snippet"), _("A snippet can't be empty."))
                return
            self.saveSnippet()
        super(Edit, self).done(result)
        self.deleteLater()

    def readSettings(self):
        data = textformats.formatData('editor')
        self.text.setFont(data.font)
        self.text.setPalette(data.palette())

    def setShortcuts(self, shortcuts):
        self._shortcuts = shortcuts
        self.updateShortcutText()
        
    def editShortcuts(self):
        mainwindow = self.parent().parent().mainwindow()
        ac = self.parent().parent().snippetActions
        action = QAction(None)
        if self._name:
            action.setShortcuts(ac.shortcuts(self._name) or [])
            skip = (ac, self._name)
            default = ac.defaults().get(self._name)
            text = snippets.title(self._name)
        else:
            skip = None
            default = None
            text = self.titleEntry.text() or _("Untitled")
        action.setText(text.replace('&', '&&'))
        if actioncollectionmanager.manager(mainwindow).editAction(self, action, default, skip):
            self.setShortcuts(action.shortcuts())
    
    def saveSnippet(self):
        index = model.model().saveSnippet(self._name,
            self.text.toPlainText(), self.titleEntry.text())
        # set snippet current in the editor that called us
        self.parent().treeView.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
        # get the name that was used
        name = model.model().name(index)
        self.parent().parent().snippetActions.setShortcuts(name, self._shortcuts)

    def slotDefaults(self):
        t = builtin.builtin_snippets[self._name]
        self.text.setPlainText(t.text)
        self.titleEntry.setText(t.title() if t.title else '')
        self.setShortcuts(self.parent().parent().snippetActions.defaults().get(self._name))


class Matcher(widgets.matcher.Matcher):
    def __init__(self, edit):
        super(Matcher, self).__init__(edit)
        self.readSettings()
        app.settingsChanged.connect(self.readSettings)
    
    def readSettings(self):
        self.format = QTextCharFormat()
        self.format.setBackground(textformats.formatData('editor').baseColors['match'])


class snippet_help(help.page):
    def title():
        return _("Snippet editor")
    
    def body():
        text = []
        text.append(_(
        "<p>Here you can edit the text of the snippet.</p>"
        "<p>If you start the first line(s) with '<code>-*- </code>' (note the space), "
        "the remainder of that line(s) defines variables like <code>name: value;</code> or "
        "simply <code>name;</code> which influence the behaviour of the snippet. "
        "The following variables can be used:</p>"))
        
        text.append("<dl>")
        text.extend(map("<dt><code>{0[0]}</code></dt><dd>{0[1]}</dd>".format, (
            ('menu',
                _("Place the snippet in the insert menu, grouped by the (optional) value.")),
            ('name',
                _("The mnemonic to type to select the snippet.")),
            ('indent: no',
                _("Do not auto-indent the snippet after inserting.")),
            ('python',
                _("Execute the snippet as a Python script. See {link}.").format(
                    link=python_snippets_help.link())),
            ('selection',
                _("One of more of the following words (separated with spaces or commas):") + " " +
                "\n".join(map("<code>{0[0]}</code>: {0[1]}".format, (
                ('yes',
                    _("Requires text to be selected.")),
                ('strip',
                    _("Adjusts the selection to not include starting and trialing whitespace.")),
                ('keep',
                    _("Selects all inserted text.")),
            )))),
        )))
        text.append("</dl>")

        text.append(_(
        "<p>The other lines of the snippet define the text to be inserted in the editor. "
        "Here, you can insert variables prefixed with a $. A double $ will be replaced with "
        "a single one. The following variables are recognized:</p>"))
        
        text.append("<dl>")
        text.extend(map("<dt><code>${0[0]}</code></dt><dd>{0[1]}</dd>".format,
            expand.documentation(expand.Expander)))
        text.append("</dl>")
        return ''.join(text)

    def children():
        return (python_snippets_help,)


class python_snippets_help(help.page):
    def title():
        return _("Python Snippets")
    
    def body():
        text = []
        text.append(_(
        "<p>Python snippets can read and should set the variable {text}. "
        "The variable {text} contains the currently selected text (which may be an "
        "empty string).</p>\n"
        "<p>You may set {text} to a string or a list of strings.</p>\n"
        "<p>Other variables that may be referenced:</p>").format(text="<code>text</code>"))
        text.append("<dl>")
        text.extend(map("<dt><code>{0[0]}</code></dt><dd>{0[1]}</dd>".format, (
            ('state',
                _("A list of strings describing the type of text the cursor is at.")),
            ('cursor',
                _("The current QTextCursor, giving access to the document. "
                  "Don't change the document through the cursor, however.")),
            ('CURSOR',
                _("When setting {text} to a list instead of a string, you can "
                  "use this value to specify the place the text cursor will be "
                  "placed after inserting the snippet.").format(text="<code>text</code>")),
            ('ANCHOR',
                _("When setting {text} to a list instead of a string, "
                  "this value can be used together with {cursor} to select text "
                  "when inserting the string parts of the list.").format(
                    text="<code>text</code>", cursor="<code>CURSOR</code>")),
        )))
        text.append("</dl>")
        return ''.join(text)




