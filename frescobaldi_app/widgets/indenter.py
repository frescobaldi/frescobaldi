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
A basic auto-indenter for a textedit widget.
"""


from __future__ import unicode_literals

import contextlib

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Indenter(QObject):
    """Install this as an event filter for a Q(Plain)TextEdit."""

    indentWidth = 2
    indentChar = ' '
    
    def __init__(self, textedit):
        super(Indenter, self).__init__(textedit)
        textedit.installEventFilter(self)
    
    def eventFilter(self, edit, ev):
        # handle Tab and Backtab
        if ev.type() == QEvent.KeyPress:
            modifiers = int(ev.modifiers() & (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META))
            if ev.text() == '\r' and modifiers == 0:
                self.newline(edit.textCursor())
                return True
            elif ev.key() == Qt.Key_Tab and modifiers == 0:
                self.indent(edit.textCursor())
                return True
            elif ev.key() == Qt.Key_Backtab and modifiers & ~Qt.SHIFT == 0:
                self.dedent(edit.textCursor())
                return True
        return False

    def newline(self, cursor):
        indent = self.getIndent(cursor)
        cursor.insertText('\n' + indent)
    
    def getIndent(self, cursor):
        text = cursor.document().findBlock(cursor.selectionStart()).text()
        return text[:len(text) - len(text.lstrip())]
        
    def indent(self, cursor):
        with editBlock(cursor):
            for block in blocks(cursor):
                cursor.setPosition(block.position())
                cursor.setPosition(block.position() + len(self.getIndent(cursor)))
                cursor.insertText(self.indentChar * self.indentWidth)
    
    def dedent(self, cursor):
        with editBlock(cursor):
            for block in blocks(cursor):
                cursor.setPosition(block.position())
                end = len(self.getIndent(cursor))
                start = max(0, end - self.indentWidth)
                if start < end:
                    cursor.setPosition(block.position() + start)
                    cursor.setPosition(block.position() + end, QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()


def blocks(cursor):
    block = cursor.document().findBlock(cursor.selectionStart())
    end = cursor.document().findBlock(cursor.selectionEnd())
    while True:
        yield block
        if block == end:
            break
        block = block.next()


@contextlib.contextmanager
def editBlock(cursor):
    """Returns a context manager to perform operations on cursor as a single undo-item."""
    cursor.beginEditBlock()
    try:
        yield
    finally:
        cursor.endEditBlock()

