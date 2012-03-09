# vimode -- Vi Mode package for QPlainTextEdit
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
ViMode implements a Vi-like mode for QPlainTextEdit.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

# the Vi modes
COMMAND = 0
VISUAL = 1
INSERT = 2


class ViMode(QObject):
    """Handles a Vi-like mode for a QPlainTextEdit."""
    def __init__(self, textedit=None):
        QObject.__init__(self)
        
        # init all internal variables
        self._mode = COMMAND
        self._textedit = None
        self._originalCursorWidth = 1
        
        self._count = 0
        self._command = ''
        
        self.setTextEdit(textedit)
    
    def setTextEdit(self, edit):
        old = self._textedit
        if edit is old:
            return
        if old:
            # disconnect old textedit
            self.clearCursor()
            old.removeEventFilter(self)
            old.cursorPositionChanged.disconnect(self.updateCursorPosition)
            old.selectionChanged.disconnect(self.updateCursorPosition)
            old.setCursorWidth(self._originalCursorWidth)
        self._textedit = edit
        if edit:
            # connect new textedit
            edit.installEventFilter(self)
            edit.cursorPositionChanged.connect(self.updateCursorPosition)
            edit.selectionChanged.connect(self.updateCursorPosition)
            self._originalCursorWidth = edit.cursorWidth()
            self.updateCursorPosition()
        self.setMode(COMMAND)
    
    def textEdit(self):
        return self._textedit
    
    def textCursor(self):
        return self._textedit.textCursor()
    
    def setMode(self, mode):
        """Sets the mode (COMMAND, VISUAL or INSERT)."""
        self._mode = mode
        self._command = ''
        self.updateCursorPosition()
        e = self.textEdit()
        if e:
            if mode is INSERT:
                e.setCursorWidth(self._originalCursorWidth)
            else:
                e.setCursorWidth(0)
    
    def mode(self):
        """Return the current mode (COMMAND, VISUAL or INSERT)."""
        return self._mode
    
    def isCommand(self):
        return self._mode is COMMAND
    
    def isInsert(self):
        return self._mode is INSERT
    
    def isVisual(self):
        return self._mode is VISUAL
    
    def updateCursorPosition(self):
        """If in command mode, shows a square cursor on the right spot."""
        cursor = self.textCursor()
        if cursor.hasSelection() and cursor.position() > cursor.anchor():
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
        else:
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        if self.mode() in (COMMAND, VISUAL):
            self.drawCursor(cursor)
        else:
            self.clearCursor()
    
    def drawCursor(self, cursor):
        """Draws the cursor position as the selection of the specified cursor."""
        es = QTextEdit.ExtraSelection()
        es.format.setBackground(self.textEdit().palette().color(QPalette.Text))
        es.format.setForeground(self.textEdit().palette().color(QPalette.Base))
        es.cursor = cursor
        self.textEdit().setExtraSelections([es])

    def clearCursor(self):
        """Removes the drawn cursor position."""
        self.textEdit().setExtraSelections([])

    def eventFilter(self, obj, ev):
        if (ev.type() in (QEvent.KeyPress, QEvent.KeyRelease) and
            ev.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta)):
            return False
        if ev.type() == QEvent.KeyPress:
            if self.isInsert():
                return self.insertKeyPressEvent(ev) or False
            return self.commandKeyPressEvent(ev) or False
        elif ev.type() == QEvent.KeyRelease:
            if self.isInsert():
                return self.insertKeyReleaseEvent(ev) or False
            return self.commandKeyReleaseEvent(ev) or False
        return False
    
    def insertKeyPressEvent(self, ev):
        """Called when a key is pressed in INSERT mode.
        
        Returns True when the key event should not be handled anymore by the
        textEdit().
        
        """
        if ev.key() == Qt.Key_Escape:
            self.setMode(COMMAND)
            return True
    
    def insertKeyReleaseEvent(self, ev):
        """Called when a key is released in INSERT mode.
        
        Returns True when the key event should not be handled anymore by the
        textEdit().
        
        """
    
    def commandKeyPressEvent(self, ev):
        """Called when a key is pressed in COMMAND or VISUAL mode.
        
        Returns True when the key event should not be handled anymore by the
        textEdit().
        
        """
        if not self._command and Qt.Key_0 <= ev.key() <= Qt.Key_9:
            self._count = self._count * 10 + (ev.key() - Qt.Key_0)
        
        return True
        
    def commandKeyReleaseEvent(self, ev):
        """Called when a key is released in COMMAND or VISUAL mode.
        
        Returns True when the key event should not be handled anymore by the
        textEdit().
        
        """

            
if __name__ == "__main__":
    a = QApplication([])
    e = QTextEdit()
    e.setCursorWidth(2)
    e.setFont(QFont("Monospace"))
    e.setPlainText("""\
some text
here another line
and here yet another
""")
    e.show()
    v = ViMode(e)
    a.exec_()

