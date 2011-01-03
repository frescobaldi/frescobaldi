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

from PyQt4.QtGui import QTextCursor


def tokens(block):
    """Returns the tokens for the given block as a (possibly empty) tuple."""
    # if block is an empty line, the highlighter doesn't run
    return block.userData().tokens if block.length() > 1 and block.userData() else ()


def state(block):
    """Returns a thawn ly.tokenize.State() object at the beginning of the given QTextBlock.
    
    The document must have a highlighter (and thus have or had at least one View).
    See highlighter.py.
    
    """
    return block.document().highlighter.state(block)


def cursor(block, token):
    """Returns a QTextCursor for the given token in the given block."""
    cursor = QTextCursor(block)
    cursor.setPosition(block.position() + token.pos)
    cursor.setPosition(block.position() + token.end, QTextCursor.KeepAnchor)
    return cursor


def selectedBlocks(cursor):
    """Yields the block(s) containing the cursor or selection."""
    c = QTextCursor(cursor)
    c.setPosition(cursor.selectionStart())
    block = c.block()
    c.setPosition(cursor.selectionEnd())
    end = c.block()
    while True:
        yield block
        if block == end:
            break
        block = block.next()
     

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
        
    def cursor(self):
        """Returns a QTextCursor for the last token."""
        return cursor(self.block, self._tokens[self._index])

    def copy(self):
        obj = object.__new__(self.__class__)
        obj.block = self.block
        obj._tokens = self._tokens
        obj._index = self._index
        return obj

