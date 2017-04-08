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
A basic auto-indenter for a textedit widget.
"""



import contextlib

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QTextCursor


class Indenter(QObject):
    """A basic indenter for a Q(Plain)TextEdit.

    When instantiated it automatically installs itself
    as an event filter for the textedit, catching some
    keypresses:

    Return:
        enters a newline and the same indent as the current line
    Tab:
        indents the current line
    Backtab:
        dedents the current line

    These instance attributes may be set:

    indentWidth:
        how many characters to indent (default 2)
    indentChar:
        which character to use (default " ")

    """

    indentWidth = 2
    indentChar = ' '

    def __init__(self, textedit):
        """Installs ourselves as event filter for textedit.

        The textedit also becomes our parent.

        """
        super(Indenter, self).__init__(textedit)
        textedit.installEventFilter(self)

    def eventFilter(self, edit, ev):
        """Handles Return, Tab and Backtab."""
        if ev.type() == QEvent.KeyPress:
            modifiers = int(ev.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
            if ev.text() == '\r' and modifiers == 0:
                cursor = edit.textCursor()
                self.newline(cursor)
                edit.setTextCursor(cursor)
                return True
            elif ev.key() == Qt.Key_Tab and modifiers == 0:
                self.indent(edit.textCursor())
                return True
            elif ev.key() == Qt.Key_Backtab and modifiers & ~Qt.SHIFT == 0:
                self.dedent(edit.textCursor())
                return True
        return False

    def newline(self, cursor):
        """Inserts a newline and then the same indent as the current line."""
        indent = self.get_indent(cursor)
        cursor.insertText('\n' + indent)

    def get_indent(self, cursor):
        """Returns the whitespace with which the current line starts."""
        text = cursor.document().findBlock(cursor.selectionStart()).text()
        return text[:len(text) - len(text.lstrip())]

    def indent(self, cursor):
        """Indents the line with the cursor or the selected lines (one step more)."""
        with compress_undo(cursor):
            for block in blocks(cursor):
                cursor.setPosition(block.position())
                cursor.setPosition(block.position() + len(self.get_indent(cursor)))
                cursor.insertText(self.indentChar * self.indentWidth)

    def dedent(self, cursor):
        """Dedents the line with the cursor or the selected lines (one step less)."""
        with compress_undo(cursor):
            for block in blocks(cursor):
                cursor.setPosition(block.position())
                end = len(self.get_indent(cursor))
                start = max(0, end - self.indentWidth)
                if start < end:
                    cursor.setPosition(block.position() + start)
                    cursor.setPosition(block.position() + end, QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()


def blocks(cursor):
    """Yields the blocks (one or more) of the cursor or its selection."""
    block = cursor.document().findBlock(cursor.selectionStart())
    end = cursor.document().findBlock(cursor.selectionEnd())
    while True:
        yield block
        if block == end:
            break
        block = block.next()


@contextlib.contextmanager
def compress_undo(cursor):
    """Returns a context manager to perform operations on cursor as a single undo-item."""
    cursor.beginEditBlock()
    try:
        yield
    finally:
        cursor.endEditBlock()

