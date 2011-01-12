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
Iterate over tokens.
"""

import contextlib

from PyQt4.QtGui import QTextCursor

import highlighter


def tokens(block):
    """Returns the tokens for the given block as a (possibly empty) tuple."""
    return highlighter.userData(block).tokens


def state(blockOrCursor):
    """Returns a thawn ly.tokenize.State() object at the beginning of the given QTextBlock.
    
    The document must have a highlighter (and thus have or had at least one View).
    See highlighter.py.
    
    If the argument is a QTextCursor, uses the current block or the first block of its selection.
    
    """
    if isinstance(blockOrCursor, QTextCursor):
        if blockOrCursor.hasSelection():
            block = blockOrCursor.document().findBlock(blockOrCursor.selectionStart())
        else:
            block = blockOrCursor.block()
    else:
        block = blockOrCursor
    return block.document().highlighter.state(block)


def update(block):
    """Retokenizes the given block, saving the tokens in the UserData.
    
    Does not update state, the highlighter will do it again to update its highlighting.
    This can be used if you change the document and want to retokenize part of it in process.
    
    """
    highlighter.updateTokens(block)


def cursor(block, token, start=0, end=None):
    """Returns a QTextCursor for the given token in the given block.
    
    If start is given the cursor will start at position start in the token
    (from the beginning of the token). Start defaults to 0.
    If end is given, the cursor will end at that position in the token (from
    the beginning of the token). End defaults to the length of the token.
    
    """
    if end is None:
        end = len(token)
    cursor = QTextCursor(block)
    cursor.setPosition(block.position() + token.pos + start)
    cursor.setPosition(block.position() + token.pos + end, QTextCursor.KeepAnchor)
    return cursor


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
     

def allBlocks(document):
    """Yields all blocks of the document."""
    block = document.firstBlock()
    while block.isValid():
        yield block
        block = block.next()


def selectedTokens(cursor, state=None):
    """Yields block, selected_tokens for every block that has selected tokens.
    
    Usage:
    
    for block, tokens in selectedTokens(cursor):
        for token in tokens:
            do_something() ...
    
    If state is given, it should be the state at the start of the block
    the selection begins. (Use state(cursor) to get that.)
    
    """
    if not cursor.hasSelection():
        return
    d = cursor.document()
    start = d.findBlock(cursor.selectionStart())
    end = d.findBlock(cursor.selectionEnd())
    block = start
    
    if state:
        def token_source():
            for token in tokens(block):
                state.followToken(token)
                yield token
    else:
        def token_source():
            for token in tokens(block):
                yield token
    
    def source_start(source):
        for token in source:
            if token.pos >= cursor.selectionStart() - start.position():
                yield token
    
    def source_end(source):
        for token in source:
            if token.end > cursor.selectionEnd() - end.position():
                break
            yield token
    
    source = source_start(token_source())
    while True:
        if block == end:
            yield block, source_end(source)
            break
        yield block, source
        block = block.next()
        source = token_source()


@contextlib.contextmanager
def editBlock(cursor, joinPrevious = False):
    """Returns a context manager to perform operations on cursor as a single undo-item."""
    cursor.joinPreviousEditBlock() if joinPrevious else cursor.beginEditBlock()
    try:
        yield
    finally:
        cursor.endEditBlock()


class TokenIterator(object):
    """An iterator over the tokens in the userData a given QTextBlock."""
    def __init__(self, block, atEnd=False):
        """Positions the token iterator at the start of the given block.
        
        If atEnd == True, the iterator is positioned past the end of the block.
        
        """
        self.block = block
        self._tokens = tokens(block)
        self._index = len(self._tokens) if atEnd else -1
    
    def forward(self, change = True):
        """Yields tokens in forward direction.
        
        If change == True, also advances to the next lines.
        
        """
        while self.block.isValid():
            while self._index + 1 < len(self._tokens):
                self._index += 1
                yield self._tokens[self._index]
            if not change:
                return
            self.__init__(self.block.next())

    def backward(self, change = True):
        """Yields tokens in backward direction.
        
        If change == True, also goes on to the previous lines.
        
        """
        while self.block.isValid():
            while self._index > 0:
                self._index -= 1
                yield self._tokens[self._index]
            if not change:
                return
            self.__init__(self.block.previous(), True)
    
    def token(self):
        """Re-returns the last yielded token."""
        return self._tokens[self._index]
        
    def cursor(self, start=0, end=None):
        """Returns a QTextCursor for the last token.
        
        If start is given the cursor will start at position start in the token
        (from the beginning of the token). Start defaults to 0.
        If end is given, the cursor will end at that position in the token (from
        the beginning of the token). End defaults to the length of the token.
        
        """
        return cursor(self.block, self._tokens[self._index], start, end)

    def copy(self):
        obj = object.__new__(self.__class__)
        obj.block = self.block
        obj._tokens = self._tokens
        obj._index = self._index
        return obj

