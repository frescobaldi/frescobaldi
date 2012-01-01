# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
A dialog to edit the keyboard shortcuts for an action.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import Qt
from PyQt4.QtGui import (
    QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QKeySequence, QLabel,
    QRadioButton, QVBoxLayout)


import app
from . import Separator
from keysequencewidget import KeySequenceWidget


class ShortcutEditDialog(QDialog):
    """A modal dialog to view and/or edit keyboard shortcuts."""
    
    def __init__(self, parent=None):
        super(ShortcutEditDialog, self).__init__(parent)
        self.setMinimumWidth(400)
        # create gui
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)
        
        top = QHBoxLayout()
        top.setSpacing(4)
        p = self.toppixmap = QLabel()
        l = self.toplabel = QLabel()
        l.setWordWrap(True)
        top.addWidget(p)
        top.addWidget(l, 1)
        layout.addLayout(top)
        
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setColumnStretch(1, 2)
        layout.addLayout(grid)
        
        self.buttonDefault = QRadioButton(self)
        self.buttonNone = QRadioButton(self)
        self.buttonCustom = QRadioButton(self)
        grid.addWidget(self.buttonDefault, 0, 0, 1, 2)
        grid.addWidget(self.buttonNone, 1, 0, 1, 2)
        grid.addWidget(self.buttonCustom, 2, 0, 1, 2)
        
        self.keybuttons = []
        self.keylabels = []
        for num in range(4):
            l = QLabel(self)
            l.setStyleSheet("margin-left: 2em;")
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            b = KeySequenceWidget(self)
            b.keySequenceChanged.connect(self.slotKeySequenceChanged)
            l.setBuddy(b)
            self.keylabels.append(l)
            self.keybuttons.append(b)
            grid.addWidget(l, num+3, 0)
            grid.addWidget(b, num+3, 1)
        
        layout.addWidget(Separator(self))
        
        b = QDialogButtonBox(self)
        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(b)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        app.translateUI(self)
    
    def translateUI(self):
        self.setWindowTitle(app.caption(_("window title", "Edit Shortcut")))
        self.buttonNone.setText(_("&No shortcut"))
        self.buttonCustom.setText(_("Use a &custom shortcut:"))
        for num in range(4):
            self.keylabels[num].setText(_("Alternative #{num}:").format(num=num) if num else _("Primary shortcut:"))
    
    def slotKeySequenceChanged(self):
        """Called when one of the keysequence buttons has changed."""
        self.buttonCustom.setChecked(True)
        
    def editAction(self, action, default=None):
        # load the action
        self._action = action
        self._default = default
        self.toplabel.setText('<p>{0}</p>'.format(
            _("Here you can edit the shortcuts for {name}").format(
                name='<br/><b>{0}</b>:'.format(action.text()))))
        self.toppixmap.setPixmap(action.icon().pixmap(32))
        shortcuts = action.shortcuts()
        self.buttonDefault.setVisible(default is not None)
        if default is not None and shortcuts == default:
            self.buttonDefault.setChecked(True)
        elif shortcuts:
            self.buttonCustom.setChecked(True)
        else:
            self.buttonNone.setChecked(True)
        for num, key in enumerate(shortcuts[:4]):
            self.keybuttons[num].setShortcut(key)
        for num in range(len(shortcuts), 4):
            self.keybuttons[num].clear()
        if default:
            ds = "; ".join(key.toString(QKeySequence.NativeText) for key in default)
        else:
            ds = _("no keyboard shortcut", "none")
        self.buttonDefault.setText(_("Use &default shortcut ({name})").format(name=ds))
        
        return self.exec_()
        
    def done(self, result):
        if result:
            shortcuts = []
            if self.buttonDefault.isChecked():
                shortcuts = self._default
            elif self.buttonCustom.isChecked():
                for num in range(4):
                    seq = self.keybuttons[num].shortcut()
                    if not seq.isEmpty():
                        shortcuts.append(seq)
            self._action.setShortcuts(shortcuts)
        super(ShortcutEditDialog, self).done(result)

