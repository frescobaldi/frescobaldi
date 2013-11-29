# cursortools.py -- QTextCursor utility functions
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
Functions manipulating QTextCursors and their selections.
"""

from __future__ import unicode_literals

import contextlib
import operator

from PyQt4.QtGui import QTextBlock, QTextBlockUserData, QTextCursor


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


class Editor(object):
    """A context manager that stores edits until it is exited.
    
    Usage:
    
    with Editor() as e:
        e.insertText(cursor, "text")
        e.removeSelectedText(cursor)
        # ... etc
    # when the code block ends, the edits will be done.
    
    All cursors are stored and should belong to the same text document.
    They update themselves if the document is changed by other means while
    the Editor instance is active.
    
    The edits will not be applied if the context is exited with an exception.
    
    """
    def __init__(self):
        self.edits = []
    
    def __enter__(self):
        return self
    
    def insertText(self, cursor, text):
        """Stores an insertText operation."""
        self.edits.append((cursor, text))
    
    def removeSelectedText(self, cursor):
        """Stores a removeSelectedText operation."""
        self.edits.append((cursor, ""))
    
    def apply(self):
        """Applies and clears the stored edits."""
        if self.edits:
            # don't use all the cursors directly, but copy and sort the ranges
            # otherwise inserts would move the cursor for adjacent edits.
            # We could also just start with the first, but that would require
            # all cursors to update their position during the process, which
            # notably slows down large edits (as there are already many cursors
            # used by the point and click feature).
            # We could also use QTextCursor.keepPositionOnInsert but that is
            # only available in the newest PyQt4 versions.
            with DocumentString(self.edits[0][0].document()) as d:
                for cursor, text in self.edits:
                    d[cursor] = text
                del self.edits[:] # delete the cursors before doing the edits
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.apply()


class DocumentString(object):
    """Represents a QTextDocument as a mutable string.
    
    You can assign using the item/slice syntax (slice step is not supported).
    Call the apply() method when done, or use it as a context manager.
    
    Usage:
    
    with DocumentString(document) as d:
        d[10:30] = text
        del d[40:56]
    
    The item can also be a QTextCursor, the selection then determines the slice,
    which is not updated when the document is changed by other means while
    the DocumentString instance is active.
    
    The changes take place on exit of the context. You can put changes in any
    order, but avoid changes on the same starting position.
    
    """
    def __init__(self, document):
        self._document = document
        self._edits = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.apply()
    
    def __setitem__(self, k, text):
        if isinstance(k, slice):
            start = k.start or 0
            end = -1 if k.stop is None else k.stop
        elif isinstance(k, QTextCursor):
            start = k.selectionStart()
            end = k.selectionEnd()
        else:
            start = k
            end = k + 1
        self._edits.append((start, end, text))
    
    def __delitem__(self, k):
        self[k] = ""
    
    def apply(self):
        """Applies and clears the stored edits."""
        if self._edits:
            c = QTextCursor(self._document)
            with compress_undo(c):
                for start, end, text in sorted(self._edits,
                            key=operator.itemgetter(0),
                            reverse=True):
                    c.setPosition(end) if end != -1 else c.movePosition(QTextCursor.End)
                    c.setPosition(start, QTextCursor.KeepAnchor)
                    c.insertText(text)
            del self._edits[:]

