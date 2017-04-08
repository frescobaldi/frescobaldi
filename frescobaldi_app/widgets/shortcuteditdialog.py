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
A dialog to edit the keyboard shortcuts for an action.
"""


from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QRadioButton,
    QVBoxLayout)


import app
from . import Separator
from .keysequencewidget import KeySequenceWidget


class ShortcutEditDialog(QDialog):
    """A modal dialog to view and/or edit keyboard shortcuts."""

    def __init__(self, parent=None, conflictCallback=None, *cbArgs):
        """conflictCallback is a optional method called when a shortcut is changed.

        cbArgs is optional arguments of the conflictCallback method.
        it should return the name of the potential conflict or a null value """

        super(ShortcutEditDialog, self).__init__(parent)
        self.conflictCallback = conflictCallback
        self.cbArgs = cbArgs
        self.setMinimumWidth(400)
        # create gui

        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)

        top = QHBoxLayout()
        top.setSpacing(4)
        p = self.toppixmap = QLabel()
        l = self.toplabel = QLabel()
        top.addWidget(p)
        top.addWidget(l, 1)
        layout.addLayout(top)
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setColumnStretch(1, 2)
        layout.addLayout(grid)

        self.buttonDefault = QRadioButton(self, toggled=self.slotButtonDefaultToggled)
        self.buttonNone = QRadioButton(self)
        self.lconflictDefault = QLabel('test')
        self.lconflictDefault.setStyleSheet("color : red;")
        self.lconflictDefault.setVisible(False)
        self.buttonCustom = QRadioButton(self)
        grid.addWidget(self.buttonDefault, 0, 0, 1, 2)
        grid.addWidget(self.lconflictDefault, 1, 0, 1, 2)
        grid.addWidget(self.buttonNone, 2, 0, 1, 2)
        grid.addWidget(self.buttonCustom, 3, 0, 1, 2)

        self.keybuttons = []
        self.keylabels = []
        self.conflictlabels = []
        for num in range(4):
            l = QLabel(self)
            l.setStyleSheet("margin-left: 2em;")
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            b = KeySequenceWidget(self, num)
            b.keySequenceChanged.connect(self.slotKeySequenceChanged)
            l.setBuddy(b)
            self.keylabels.append(l)
            self.keybuttons.append(b)
            grid.addWidget(l, num+4+num, 0)
            grid.addWidget(b, num+4+num, 1)
            lconflict = QLabel()
            lconflict.setStyleSheet("color : red;")
            self.conflictlabels.append(lconflict)
            lconflict.setVisible(False)
            grid.addWidget(lconflict, num+5+num, 0, 1, 2, Qt.AlignHCenter)

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

    def slotKeySequenceChanged(self, num):
        """Called when one of the keysequence buttons has changed."""
        self.checkConflict(num)
        self.buttonCustom.setChecked(True)

    def slotButtonDefaultToggled(self, val):
        if self.conflictCallback is not None:
            if not val:
                self.lconflictDefault.setVisible(False)
            else:
                if self._default:
                    conflictList = []
                    for s in self._default:
                        conflictName = self.conflictCallback(s, *self.cbArgs)
                        if conflictName:
                            conflictList.append(conflictName)
                    if conflictList:
                        text = _("Conflict with: {name}").format(
                            name="<b>{0}</b>".format(', '.join(conflictList)))
                        self.lconflictDefault.setText(text)
                        self.lconflictDefault.setVisible(True)
            QTimer.singleShot(0, self.adjustSize)

    def checkConflict(self, num):
        if self.conflictCallback is not None:
            conflictName = self.conflictCallback(self.keybuttons[num].shortcut(), *self.cbArgs)
            if conflictName:
                text = _("Conflict with: {name}").format(
                    name="<b>{0}</b>".format(conflictName))
                self.conflictlabels[num].setText(text)
                self.conflictlabels[num].setVisible(True)
            else:
                self.conflictlabels[num].setVisible(False)
            QTimer.singleShot(0, self.adjustSize)

    def editAction(self, action, default=None):
        # load the action
        self._action = action
        self._default = default
        self.toplabel.setText('<p>{0}</p>'.format(
            _("Here you can edit the shortcuts for {name}").format(
                name='<br/><b>{0}</b>:'.format(action.text()))))
        self.toppixmap.setPixmap(action.icon().pixmap(32))
        shortcuts = action.shortcuts()
        self.buttonDefault.setVisible(bool(default))
        if default is not None and shortcuts == default:
            self.buttonDefault.setChecked(True)
        else:
            if shortcuts:
                self.buttonCustom.setChecked(True)
                for num, key in enumerate(shortcuts[:4]):
                    self.keybuttons[num].setShortcut(key)
                    self.checkConflict(num)
            else:
                self.buttonNone.setChecked(True)

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

