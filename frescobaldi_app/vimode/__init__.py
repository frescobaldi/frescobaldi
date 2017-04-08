# vimode -- Vi Mode package for QPlainTextEdit
#
# Copyright (c) 2012 by Wilbert Berendsen
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


from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import QApplication, QTextEdit

# the Vi modes
NORMAL = 0
VISUAL = 1
INSERT = 2
REPLACE = 3


class ViMode(QObject):
    """Handles a Vi-like mode for a QPlainTextEdit."""
    def __init__(self, textedit=None):
        QObject.__init__(self)

        # init all internal variables
        self._mode = None
        self._handlers = [None] * 4
        self._textedit = None
        self._originalCursorWidth = 1

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
        self.setMode(NORMAL)
        if edit:
            self.updateCursorPosition()

    def textEdit(self):
        return self._textedit

    def setMode(self, mode):
        """Sets the mode (NORMAL, VISUAL, INSERT or REPLACE)."""
        if mode is self._mode:
            return
        assert mode in (NORMAL, VISUAL, INSERT, REPLACE)
        if self._mode is not None and self.handler():
            self.handler().leave()
        self._mode = mode
        if self._handlers[mode] is None:
            self._handlers[mode] = self.createModeHandler(mode)
        self.handler().enter()
        self.updateCursorPosition()

    def mode(self):
        """Return the current mode (NORMAL, VISUAL, INSERT or REPLACE)."""
        return self._mode

    def isNormal(self):
        return self._mode is NORMAL

    def isVisual(self):
        return self._mode is VISUAL

    def isInsert(self):
        return self._mode is INSERT

    def isReplace(self):
        return self._mode is REPLACE

    def createModeHandler(self, mode):
        """Returns a Handler for the specified mode."""
        if mode == NORMAL:
            from . import normal
            return normal.NormalMode(self)
        elif mode == VISUAL:
            from . import visual
            return visual.VisualMode(self)
        elif mode == INSERT:
            from . import insert
            return insert.InsertMode(self)
        elif mode == REPLACE:
            from . import replace
            return replace.ReplaceMode(self)

    def handler(self):
        """Returns the current mode handler."""
        return self._handlers[self._mode]

    def updateCursorPosition(self):
        """If in command mode, shows a square cursor on the right spot."""
        self.handler().updateCursorPosition()

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
            return self.handler().handleKeyPress(ev) or False
        return False



def test():
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

