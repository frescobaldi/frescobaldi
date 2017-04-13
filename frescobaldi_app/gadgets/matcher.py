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
A basic parenthesis/brace character matcher for a textedit widget.
"""


from PyQt5.QtCore import QObject, QRegExp, Qt, QTimer
from PyQt5.QtGui import QTextCharFormat, QTextCursor, QTextDocument
from PyQt5.QtWidgets import QTextEdit


class Matcher(QObject):
    """Highlights matching characters in a textedit.

    The following attributes are available at the class level,
    and may be overridden by setting them as instance attributes:

    matchPairs: a string of characters that match in pairs with each other
                default: "{}()[]"
    format:     a QTextCharFormat used to highlight matching characters with
                default: a red foreground color
    time:       how many milliseconds to show the highlighting (0=forever)
                default: 2000

    """

    matchPairs = "{}()[]"
    format = QTextCharFormat()
    format.setForeground(Qt.red)
    time = 2000

    def __init__(self, edit):
        """Initialize the Matcher; edit is a Q(Plain)TextEdit instance."""
        super(Matcher, self).__init__(edit)
        self._timer = QTimer(singleShot=True, timeout=self.clear)
        edit.cursorPositionChanged.connect(self.slotCursorPositionChanged)

    def edit(self):
        """Returns our Q(Plain)TextEdit."""
        return self.parent()

    def slotCursorPositionChanged(self):
        """Called whenever the cursor position changes.

        Highlights matching characters if the cursor is at one of them.

        """
        cursor = self.edit().textCursor()
        block = cursor.block()
        text = block.text()

        # try both characters at the cursor
        col = cursor.position() - block.position()
        end = col + 1
        col = max(0, col - 1)
        for c in text[col:end]:
            if c in self.matchPairs:
                break
            col += 1
        else:
            self.clear()
            return

        # the cursor is at a character from matchPairs
        i = self.matchPairs.index(c)
        cursor.setPosition(block.position() + col)

        # find the matching character
        new = QTextCursor(cursor)
        if i & 1:
            # look backward
            match = self.matchPairs[i-1]
            flags = QTextDocument.FindBackward
        else:
            # look forward
            match = self.matchPairs[i+1]
            flags = QTextDocument.FindFlags()
            new.movePosition(QTextCursor.Right)

        # search, also nesting
        rx = QRegExp(QRegExp.escape(c) + '|' + QRegExp.escape(match))
        nest = 0
        while nest >= 0:
            new = cursor.document().find(rx, new, flags)
            if new.isNull():
                self.clear()
                return
            nest += 1 if new.selectedText() == c else -1
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        self.highlight([cursor, new])

    def highlight(self, cursors):
        """Highlights the selections of the specified QTextCursor instances."""
        selections = []
        for cursor in cursors:
            es = QTextEdit.ExtraSelection()
            es.cursor = cursor
            es.format = self.format
            selections.append(es)
        self.edit().setExtraSelections(selections)
        if self.time and selections:
            self._timer.start(self.time)

    def clear(self):
        """Removes the highlighting."""
        self.edit().setExtraSelections([])


