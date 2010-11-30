# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
A widget to enter a keyboard shortcut.

Loosely based on kkeysequencewidget.cpp from KDE :-)

"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
)

class KeySequenceWidget(QWidget):

    keySequenceChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super(KeySequenceWidget, self).__init__(parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)
        
        self.button = KeySequenceButton(self)
        self.clearButton = QToolButton(self)
        self.clearButton.setIcon(icons.get("edit-clear-locationbar-rtl"))
        layout.addWidget(self.button)
        layout.addWidget(self.clearButton)
        
        self.clearButton.clicked.connect(self.clear)
        self.translateUI()
        
    def translateUI(self):
        self.clearButton.setToolTip(_("Click to clear the key sequence."))
        
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
            self.keySequenceChanged.emit()

    def setModifierlessAllowed(self, allow):
        self.button._modifierlessAllowed = allow
        
    def isModifierlessAllowed(self):
        return self.button._modifierlessAllowed


class KeySequenceButton(QPushButton):
    
    def __init__(self, parent=None):
        super(KeySequenceButton, self).__init__(parent)
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
        return self._seq
    
    def updateDisplay(self):
        if self._isrecording:
            s = self._recseq.toString().replace('&', '&&')
            if self._modifiers:
                if s: s += ","
                if self._modifiers & Qt.META:  s += "Meta+"
                if self._modifiers & Qt.CTRL:  s += "Ctrl+"
                if self._modifiers & Qt.ALT:   s += "Alt+"
                if self._modifiers & Qt.SHIFT: s += "Shift+"
            elif self._recseq.isEmpty():
                s = _("Input")
            s += " ..."
        else:
            s = self._seq.toString().replace('&', '&&')
        self.setText(s)

    def isRecording(self):
        return self._isrecording
        
    def event(self, ev):
        if self._isrecording:
            # prevent Qt from special casing Tab and Backtab
            if ev.type() == QEvent.KeyPress:
                self.keyPressEvent(ev)
                return True
        return super(KeySequenceButton, self).event(ev)
        
    def keyPressEvent(self, ev):
        if not self._isrecording:
            return super(KeySequenceButton, self).keyPressEvent(ev)
        modifiers = int(ev.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
        ev.accept()
        
        key = ev.key()
        
        # check if key is a modifier or a character key without modifier (and if that is allowed)
        if (
            # don't append the key if the key is -1 (garbage) or a modifier ...
            key not in (-1, Qt.Key_AltGr, Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_Menu)
            # or if this is the first key and without modifier and modifierless keys are not allowed
            and (self._modifierlessAllowed
                 or self._recseq.count() > 0
                 or modifiers & ~Qt.SHIFT
                 or not (ev.text() or key in (Qt.Key_Return, Qt.Key_Space, Qt.Key_Tab, Qt.Key_Backtab,
                                              Qt.Key_Backspace, Qt.Key_Delete)))):
            
            # change Shift+Backtab into Shift+Tab
            if key == Qt.Key_Backtab and modifiers & Qt.SHIFT:
                key = Qt.Key_Tab | modifiers
            # remove the Shift modifier if it doen't make sense
            elif (Qt.Key_F1 <= key <= Qt.Key_F35
                  or (ev.text() and ev.text().isalpha())
                  or key in (
                        Qt.Key_Return,
                        Qt.Key_Space,
                        Qt.Key_Backspace,
                        Qt.Key_Escape,
                        Qt.Key_Print,
                        Qt.Key_ScrollLock,
                        Qt.Key_Pause,
                        Qt.Key_PageUp,
                        Qt.Key_PageDown,
                        Qt.Key_Insert,
                        Qt.Key_Delete,
                        Qt.Key_Home,
                        Qt.Key_End,
                        Qt.Key_Up,
                        Qt.Key_Down,
                        Qt.Key_Left,
                        Qt.Key_Right,
                    )):
                key = key | modifiers
            else:
                key = key | (modifiers & ~Qt.SHIFT)
            
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
            return super(KeySequenceButton, self).keyReleaseEvent(ev)
        modifiers = int(ev.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
        ev.accept()
        
        self._modifiers = modifiers
        self.controlTimer()
        self.updateDisplay()
    
    def hideEvent(self, ev):
        if self._isrecording:
            self.cancelRecording()
        super(KeySequenceButton, self).hideEvent(ev)
        
    def controlTimer(self):
        if self._modifiers or self._recseq.isEmpty():
            self._timer.stop()
        else:
            self._timer.start(600)
    
    def startRecording(self):
        self.setDown(True)
        self.setStyleSheet("QPushButton { text-align: left; }")
        self._isrecording = True
        self._recseq = QKeySequence()
        self._modifiers = int(QApplication.keyboardModifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
        self.grabKeyboard()
        self.updateDisplay()
        
    def doneRecording(self):
        self._seq = self._recseq
        self.cancelRecording()
        self.parentWidget().keySequenceChanged.emit()
        
    def cancelRecording(self):
        if not self._isrecording:
            return
        self.setDown(False)
        self.setStyleSheet(None)
        self._isrecording = False
        self.releaseKeyboard()
        self.updateDisplay()


    