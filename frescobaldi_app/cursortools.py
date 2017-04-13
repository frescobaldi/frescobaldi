# cursortools.py -- QTextCursor utility functions
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
Functions manipulating QTextCursors and their selections.
"""


import contextlib
import operator

from PyQt5.QtGui import QTextBlock, QTextBlockUserData, QTextCursor


def block(cursor):
    """Returns the cursor's block.

    If the cursor has a selection, returns the block the selection starts in
    (regardless of the cursor's position()).

    """
    if cursor.hasSelection():
        return cursor.document().findBlock(cursor.selectionStart())
    return cursor.block()


def blocks(cursor):
    """Yields the block(s) containing the cursor or selection."""
    d = cursor.document()
    block = d.findBlock(cursor.selectionStart())
    end = d.findBlock(cursor.selectionEnd())
    while True:
        yield block
        if block == end:
            break
        block = block.next()


def contains(c1, c2):
    """Returns True if cursor2's selection falls inside cursor1's."""
    return (c1.selectionStart() <= c2.selectionStart()
            and c1.selectionEnd() >= c2.selectionEnd())


def forwards(block, until=QTextBlock()):
    """Yields the block and all following blocks.

    If until is a valid block, yields the blocks until the specified block.

    """
    if until.isValid():
        while block.isValid() and block <= until:
            yield block
            block = block.next()
    else:
        while block.isValid():
            yield block
            block = block.next()


def backwards(block, until=QTextBlock()):
    """Yields the block and all preceding blocks.

    If until is a valid block, yields the blocks until the specified block.

    """
    if until.isValid():
        while block.isValid() and block >= until:
            yield block
            block = block.previous()
    else:
        while block.isValid():
            yield block
            block = block.previous()


def all_blocks(document):
    """Yields all blocks of the document."""
    return forwards(document.firstBlock())


def partition(cursor):
    """Returns a three-tuple of strings (before, selection, after).

    'before' is the text before the cursor's position or selection start,
    'after' is the text after the cursor's position or selection end,
    'selection' is the selected text.

    before and after never contain a newline.

    """
    start = cursor.document().findBlock(cursor.selectionStart())
    end = cursor.document().findBlock(cursor.selectionEnd())
    before = start.text()[:cursor.selectionStart() - start.position()]
    selection = cursor.selection().toPlainText()
    after = end.text()[cursor.selectionEnd() - end.position():]
    return before, selection, after


@contextlib.contextmanager
def compress_undo(cursor, join_previous = False):
    """Returns a context manager to perform operations on cursor as a single undo-item."""
    cursor.joinPreviousEditBlock() if join_previous else cursor.beginEditBlock()
    try:
        yield
    finally:
        cursor.endEditBlock()


@contextlib.contextmanager
def keep_selection(cursor, edit=None):
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


def strip_selection(cursor, chars=None):
    """Adjusts the selection of the cursor just like Python's strip().

    If there is no selection or the selection would vanish completely,
    nothing is done.

    """
    if not cursor.hasSelection():
        return
    text = cursor.selection().toPlainText()
    if not text.strip(chars):
        return
    l = len(text) - len(text.lstrip(chars))
    r = len(text) - len(text.rstrip(chars))
    s = cursor.selectionStart() + l
    e = cursor.selectionEnd() - r
    if cursor.position() < cursor.anchor():
        s, e = e, s
    cursor.setPosition(s)
    cursor.setPosition(e, QTextCursor.KeepAnchor)


def strip_indent(cursor):
    """Moves the cursor in its block to the first non-space character."""
    text = cursor.block().text()
    pos = len(text) - len(text.lstrip())
    cursor.setPosition(cursor.block().position() + pos)


def insert_select(cursor, text):
    """Inserts text and then selects all inserted text in the cursor."""
    pos = cursor.selectionStart()
    cursor.insertText(text)
    new = cursor.position()
    cursor.setPosition(pos)
    cursor.setPosition(new, QTextCursor.KeepAnchor)


def isblank(block):
    """Returns True if the block is an empty or blank line."""
    text = block.text()
    return not text or text.isspace()


def isblank_before(cursor):
    """Returns True if there's no text on the current line before the cursor."""
    if cursor.atBlockStart():
        return True
    text = cursor.block().text()[:cursor.position() - cursor.block().position()]
    return not text or text.isspace()


def isblank_after(cursor):
    """Returns True if there's no text on the current line after the cursor."""
    if cursor.atBlockEnd():
        return True
    text = cursor.block().text()[cursor.position() - cursor.block().position():]
    return not text or text.isspace()


def next_blank(block):
    """Returns the next block that is the first block of one or more blank blocks."""
    bb = forwards(block)
    for b in bb:
        if not isblank(b):
            for b in bb:
                if isblank(b):
                    return b


def previous_blank(block):
    """Returns the previous block that is the first block of one or more blank blocks."""
    bb = backwards(block)
    for b in bb:
        if not isblank(b):
            for b in bb:
                if isblank(b):
                    for b in bb:
                        if not isblank(b):
                            b = b.next()
                            break
                    return b


def data(block):
    """Get the block's QTextBlockUserData, creating it if necessary."""
    data = block.userData()
    if not data:
        data = QTextBlockUserData()
        block.setUserData(data)
    return data


