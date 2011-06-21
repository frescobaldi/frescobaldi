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
import icons
import textformats
import widgets

from . import model
from . import snippets
from . import builtin
from . import expand


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
        self.text = QPlainTextEdit()
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
        
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        if name and name in builtin.builtin_snippets:
            b.setStandardButtons(buttons | QDialogButtonBox.RestoreDefaults)
            b.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.slotDefaults)
        else:
            b.setStandardButtons(buttons)
        
        Highlighter(self.text.document())
        
        if name:
            self.titleEntry.setText(snippets.title(name, False) or '')
            self.text.setPlainText(snippets.text(name))
            ac = self.parent().parent().snippetActions
            self.setShortcuts(ac.shortcuts(name))
        else:
            self.text.setPlainText(text)
            self.setShortcuts(None)
        
        app.translateUI(self)
        
        self.restoreSize()
        self.readSettings()
        app.settingsChanged.connect(self.readSettings)
        self.show()
        
    def translateUI(self):
        title = _("Edit Snippet") if self._name else _("New Snippet")
        self.setWindowTitle(app.caption(title))
        self.topLabel.setText(_("Snippet Text:"))
        self.titleLabel.setText(_("Title:"))
        self.shortcutLabel.setText(_("Shortcut:"))
        self.updateShortcutText()
        self.text.setWhatsThis(whatsThisText())
            
    
    def updateShortcutText(self):
        if not self._shortcuts:
            self.shortcutButton.setText(_("None"))
        else:
            key = self._shortcuts[0].toString()
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
        self.storeSize()

    def storeSize(self):
        QSettings().setValue("snippettool/editor/size", self.size())
        
    def restoreSize(self):
        self.resize(QSettings().value("snippettool/editor/size", QSize(400, 300)))
    
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


class Highlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super(Highlighter, self).__init__(document)
        self.readSettings()
        app.settingsChanged.connect(self.readSettingsAgain)
        
    def readSettings(self):
        self._styles = textformats.formatData('editor').defaultStyles
        
    def readSettingsAgain(self):
        self.readSettings()
        self.rehighlight()
        
    def highlightBlock(self, text):
        if text.startswith('-*- '):
            self.setFormat(0, 3, self._styles['keyword'])
            for m in snippets._variables_re.finditer(text):
                self.setFormat(m.start(1), m.end(1)-m.start(1), self._styles['variable'])
                if m.group(2):
                    self.setFormat(m.start(2), m.end(2)-m.start(2), self._styles['value'])
        else:
            for m in snippets._expansions_re.finditer(text):
                self.setFormat(m.start(), m.end()-m.start(), self._styles['escape'])


def whatsThisText():
    """Returns the What's This text for the snippet edit widget."""
    text = []
    text.append(_(
    "<p>Here you can edit the text of the snippet.</p>"
    "<p>If you start the first line(s) with '<code>-*- </code>' (note the space), "
    "the remainder of that line(s) defines variables like <code>name: value;</code> or "
    "simply <code>name;</code> which influence the behaviour of the snippet. "
    "The following variables currently have a meaning:</p>"))
    
    text.append("<dl>")
    text.extend("<dt><code>{0}</code></dt><dd>{1}</dd>".format(name, desc) for name, desc in (
        ('menu', _("Place the snippet in the insert menu, grouped by the (optional) value.")),
        ('name', _("The mnemonic to type to select the snippet.")),
    ))
    text.append("</dl>")

    text.append(_(
    "<p>The other lines of the snippet define the text to be inserted in the editor. "
    "Here, you can insert variables prefixed with a $. A double $ will be replaced with "
    "a single one. The following variables are recognized:</p>"))
    
    text.append("<dl>")
    text.extend("<dt><code>${0}</code></dt><dd>{1}</dd>".format(name, doc) for name, doc in
        expand.documentation(expand.ExpanderBasic))
    text.append("</dl>")
    return ''.join(text)



