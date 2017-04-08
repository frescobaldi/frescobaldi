# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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
Dialog for the Mode shift functionality.
"""


from fractions import Fraction

from PyQt5.QtCore import QSettings, QSize
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QLineEdit, QWidget)

import app
import userguide
import qutil

# Mode definitions
modes = {
'Major': ((0,0), (1,1), (2,2), (3, Fraction(5, 2)), (4, Fraction(7, 2)),
          (5, Fraction(9, 2)), (6, Fraction(11, 2))),
'Minor (harmonic)': ((0,0), (1,1), (2, Fraction(3, 2)), (3, Fraction(5, 2)),
          (4, Fraction(7, 2)), (5, 4), (6, Fraction(11, 2))),
'Minor (natural)': ((0,0), (1,1), (2, Fraction(3, 2)), (3, Fraction(5, 2)),
             (4, Fraction(7, 2)), (5, 4), (6,5)),
'Dorian': ((0,0), (1,1), (2, Fraction(3, 2)), (3, Fraction(5, 2)),
           (4, Fraction(7, 2)), (5, Fraction(9, 2)), (6,5)),
'Phrygian': ((0,0), (1, Fraction(1, 2)), (2, Fraction(3, 2)),
             (3, Fraction(5, 2)), (4, Fraction(7, 2)), (5,4), (6,5)),
'Lydian': ((0,0), (1,1), (2,2), (3,3), (4, Fraction(7, 2)),
           (5, Fraction(9, 2)), (6, Fraction(11, 2))),
'Mixolydian': ((0,0), (1,1), (2,2), (3, Fraction(5, 2)), (4, Fraction(7, 2)),
               (5, Fraction(9, 2)), (6,5)),
'Locrian': ((0,0), (1, Fraction(1, 2)), (2, Fraction(3, 2)),
             (3, Fraction(5, 2)), (4, 3), (5,4), (6,5)),
'Phrygian dominant': ((0,0), (1, Fraction(1, 2)), (2, 2),
             (3, Fraction(5, 2)), (4, Fraction(7, 2)), (5,4), (6,5)),
'Hungarian minor': ((0,0), (1,1), (2, Fraction(3, 2)), (3,3),
          (4, Fraction(7, 2)), (5, 4), (6, Fraction(11, 2))),
'Double harmonic major': ((0,0), (1, Fraction(1, 2)), (2, 2), (3, Fraction(5, 2)),
                          (4, Fraction(7, 2)), (5,4), (6, Fraction(11, 2))),
'Persian': ((0,0), (1, Fraction(1, 2)), (2, 2), (3, Fraction(5, 2)),
            (4, 3), (5,4), (6, Fraction(11, 2))),
'Diminished (octatonic)': ((0,0), (1,1), (2, Fraction(3, 2)), (3, Fraction(5, 2)), (4, 3),
        (5,4), (5, Fraction(9, 2)), (6, Fraction(11, 2))),
'Whole tone (hexatonic)': ((0,0), (1,1), (2,2), (3,3), (4,4), (6,5)),
'Yo (pentatonic)': ((0,0), (1,1), (3, Fraction(5, 2)), (4, Fraction(7, 2)), (6,5))
}


class ModeShiftDialog(QDialog):

    def __init__(self, parent=None):
        super(ModeShiftDialog, self).__init__(parent)

        mainLayout = QGridLayout()
        self.setLayout(mainLayout)

        self.keyLabel = QLabel()
        self.keyInput = QLineEdit()
        self.modeCombo = QComboBox()
        self.modeLabel = QLabel()

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        userguide.addButton(self.buttons, "mode_shift")

        for m in sorted(modes.keys()):
            self.modeCombo.addItem(m)

        mainLayout.addWidget(self.keyLabel, 0, 0, 1, 1)
        mainLayout.addWidget(self.keyInput, 0, 1, 1, 1)
        mainLayout.addWidget(self.modeLabel, 1, 0, 1, 1)
        mainLayout.addWidget(self.modeCombo, 1, 1, 1, 1)
        mainLayout.addWidget(self.buttons, 9, 0, 2, 2)

        app.translateUI(self)
        qutil.saveDialogSize(self, "mode_shift/dialog/size", QSize(80, 60))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.keyInput.textEdited.connect(self.readKeyInput)
        self.modeCombo.currentIndexChanged.connect(self.readSettings)

        self.loadSettings()

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Mode Shift")))
        self.keyLabel.setText(_("Key:"))
        self.modeLabel.setText(_("Mode:"))
        self.buttons.button(QDialogButtonBox.Ok).setText(_("shift pitches"))
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def setKeyValidator(self, validate):
        """Set function that validates the key input."""
        keyValidator = KeyValidator()
        keyValidator.setValidateFunc(validate)
        self.keyInput.setValidator(keyValidator)

    def readSettings(self):
        """Reads the current settings."""
        self._currentKey = self.keyInput.text()
        self._currentMode = self.modeCombo.currentText()

    def readKeyInput(self):
        """Read the key input and check if it's acceptable."""
        if self.keyInput.hasAcceptableInput():
            self.readSettings()
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def getMode(self):
        """Returns the chosen mode."""
        return self._currentKey, modes[self._currentMode]

    def loadSettings(self):
        """ get users previous settings """
        s = QSettings()
        s.beginGroup('mode_shift')
        key = s.value('key', "", str)
        self.keyInput.setText(key)
        index = s.value('mode', 0, int)
        self.modeCombo.setCurrentIndex(index)
        self.readKeyInput()

    def saveSettings(self):
        """ save users last settings """
        s = QSettings()
        s.beginGroup('mode_shift')
        s.setValue('key', self._currentKey)
        s.setValue('mode', self.modeCombo.currentIndex())


class KeyValidator(QValidator):

    def __init__(self, parent=None):
        super(KeyValidator, self).__init__(parent)

    def setValidateFunc(self, func):
        self._func = func

    def validate(self, text, pos):
        if text:
            if self._func(text):
                return (QValidator.Acceptable, text, pos)
            elif len(text) > 3:
                return (QValidator.Invalid, text, pos)
        return (QValidator.Intermediate, text, pos)

