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
Function manipulating QTextCursors and their selections.
"""

from __future__ import unicode_literals

import contextlib

from PyQt4.QtGui import QTextCursor


def allBlocks(document):
    """Yields all blocks of the document."""
    block = document.firstBlock()
    while block.isValid():
        yield block
        block = block.next()


def selectedBlocks(cursor):
    """Yields the block(s) containing the cursor or selection."""
    d = cursor.document()
    block = d.findBlock(cursor.selectionStart())
    end = d.findBlock(cursor.selectionEnd())
    while True:
        yield block
        if block == end:
            break
        block = block.next()
     

@contextlib.contextmanager
def editBlock(cursor, joinPrevious = False):
    """Returns a context manager to perform operations on cursor as a single undo-item."""
    cursor.joinPreviousEditBlock() if joinPrevious else cursor.beginEditBlock()
    try:
        yield
    finally:
        cursor.endEditBlock()


@contextlib.contextmanager
def keepSelection(cursor, edit=None):
    """Performs operations inside the selection and restore the selection afterwards.
    
    If edit is given, call setTextCursor(cursor) on the Q(Plain)TextEdit afterwards.
    
    """
    start, end, pos = cursor.selectionStart(), cursor.selectionEnd(), cursor.position()
    cur2 = QTextCursor(cursor)
    cur2.setPosition(end)
    
    try:
        yield
    finally:
        if pos == start:
            cursor.setPosition(cur2.position())
            cursor.setPosition(start, QTextCursor.KeepAnchor)
        else:
            cursor.setPosition(start)
            cursor.setPosition(cur2.position(), QTextCursor.KeepAnchor)
        if edit:
            edit.setTextCursor(cursor)


def stripSelection(cursor):
    """Adjusts the selection to not include whitespace on both ends."""
    if not cursor.hasSelection():
        return
    text = cursor.selection().toPlainText()
    if text.isspace():
        return
    start, end, pos = cursor.selectionStart(), cursor.selectionEnd(), cursor.position()
    atStart = start == pos
    
    for c in text:
        if c.isspace():
            start += 1
        else:
            break
    for c in text[::-1]:
        if c.isspace():
            end -= 1
        else:
            break
    if atStart:
        start, end = end, start
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.KeepAnchor)


