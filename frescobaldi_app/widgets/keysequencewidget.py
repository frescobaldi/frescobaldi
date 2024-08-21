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
A widget to enter a keyboard shortcut.

Loosely based on kkeysequencewidget.cpp from KDE :-)

"""


from PyQt6.QtCore import QKeyCombination, QEvent, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QPushButton, QToolButton, QWidget)

import app
import icons

from . import ClearButton


class KeySequenceWidget(QWidget):

    keySequenceChanged = pyqtSignal(int)

    def __init__(self, parent=None, num=0):
        super().__init__(parent)
        self._num = num
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        self.button = KeySequenceButton(self)
        self.clearButton = ClearButton(self, iconSize=QSize(16, 16))
        layout.addWidget(self.button)
        layout.addWidget(self.clearButton)

        self.clearButton.clicked.connect(self.clear)
        app.translateUI(self)

    def translateUI(self):
        self.button.setToolTip(_("Start recording a key sequence."))
        self.clearButton.setToolTip(_("Clear the key sequence."))

    def setShortcut(self, shortcut):
        """Sets the initial shortcut to display."""
        self.button.setKeySequence(shortcut)

    def shortcut(self):
        """Returns the currently set key sequence."""
        return self.button.keySequence()

    def clear(self):
        """Empties the displayed shortcut."""
        if self.button.isRecording():
            self.button.cancelRecording()
        if not self.button.keySequence().isEmpty():
            self.button.setKeySequence(QKeySequence())
            self.keySequenceChanged.emit(self._num)

    def setModifierlessAllowed(self, allow):
        self.button._modifierlessAllowed = allow

    def isModifierlessAllowed(self):
        return self.button._modifierlessAllowed

    def num(self):
        return self._num


class KeySequenceButton(QPushButton):

    ADMITTED_MODIFIERS = Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(icons.get("configure"))
        self._modifierlessAllowed = False
        self._seq = QKeySequence()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._isrecording = False
        self.clicked.connect(self.startRecording)
        self._timer.timeout.connect(self.doneRecording)

    def setKeySequence(self, seq):
        self._seq = seq
        self.updateDisplay()

    def keySequence(self):
        if self._isrecording:
            self.doneRecording()
        return self._seq

    def updateDisplay(self):
        if self._isrecording:
            s = self._recseq.toString(QKeySequence.SequenceFormat.NativeText).replace('&', '&&')
            if self._modifiers:
                if s: s += ","
                s += QKeySequence(self._modifiers.value).toString(QKeySequence.SequenceFormat.NativeText)
            elif self._recseq.isEmpty():
                s = _("Input")
            s += " ..."
        else:
            s = self._seq.toString(QKeySequence.SequenceFormat.NativeText).replace('&', '&&')
        self.setText(s)

    def isRecording(self):
        return self._isrecording

    def event(self, ev):
        if self._isrecording:
            # prevent Qt from special casing Tab and Backtab
            if ev.type() == QEvent.Type.KeyPress:
                self.keyPressEvent(ev)
                return True
        return super().event(ev)

    def keyPressEvent(self, ev):
        if not self._isrecording:
            return super().keyPressEvent(ev)
        if ev.isAutoRepeat():
            return
        modifiers = ev.modifiers() & self.ADMITTED_MODIFIERS
        ev.accept()

        key = Qt.Key(ev.key())
        # check if key is a modifier or a character key without modifier (and if that is allowed)
        if (
            # don't append the key if the key is -1 (garbage) or a modifier ...
            key.value != -1 and
            key not in (Qt.Key.Key_AltGr, Qt.Key.Key_Shift, Qt.Key.Key_Control,
                            Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_Menu)
            # or if this is the first key and without modifier and modifierless keys are not allowed
            and (self._modifierlessAllowed
                 or self._recseq.count() > 0
                 or modifiers & ~Qt.KeyboardModifier.ShiftModifier
                 or not ev.text()
                 or (modifiers & Qt.KeyboardModifier.ShiftModifier
                     and key in (Qt.Key.Key_Return, Qt.Key.Key_Space, Qt.Key.Key_Tab, Qt.Key.Key_Backtab,
                                 Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Escape)))):
            # change Shift+Backtab into Shift+Tab
            if key == Qt.Key.Key_Backtab and modifiers & Qt.KeyboardModifier.ShiftModifier:
                key = QKeyCombination(modifiers, Qt.Key.Key_Tab)
            # remove the Shift modifier if it doesn't make sense
#            elif (Qt.Key.Key_Exclam <= key <= Qt.Key.Key_At
#                  or Qt.Key.Key_Z < key <= 0x0ff):
#                key = key | (modifiers & ~Qt.Modifier.SHIFT)
            else:
                key = QKeyCombination(modifiers, key)

            # append max. 4 keystrokes
            if self._recseq.count() < 4:
                l = list(self._recseq)
                l.append(key)
                self._recseq = QKeySequence(*l)

        self._modifiers = modifiers
        self.controlTimer()
        self.updateDisplay()

    def keyReleaseEvent(self, ev):
        if not self._isrecording:
            return super().keyReleaseEvent(ev)
        modifiers = ev.modifiers() & self.ADMITTED_MODIFIERS
        ev.accept()

        self._modifiers = modifiers
        self.controlTimer()
        self.updateDisplay()

    def hideEvent(self, ev):
        if self._isrecording:
            self.cancelRecording()
        super().hideEvent(ev)

    def controlTimer(self):
        if self._modifiers or self._recseq.isEmpty():
            self._timer.stop()
        else:
            self._timer.start(600)

    def startRecording(self):
        self.setFocus(Qt.FocusReason.OtherFocusReason) # because of QTBUG 17810
        self.setDown(True)
        self.setStyleSheet("text-align: left;")
        self._isrecording = True
        self._recseq = QKeySequence()
        self._modifiers = QApplication.keyboardModifiers() & self.ADMITTED_MODIFIERS
        self.grabKeyboard()
        self.updateDisplay()

    def doneRecording(self):
        self._seq = self._recseq
        self.cancelRecording()
        self.clearFocus()
        self.parentWidget().keySequenceChanged.emit(self.parentWidget().num())

    def cancelRecording(self):
        if not self._isrecording:
            return
        self.setDown(False)
        self.setStyleSheet(None)
        self._isrecording = False
        self.releaseKeyboard()
        self.updateDisplay()


