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


class TokenIterator(object):
    """An iterator over the tokens in the userData a given QTextBlock."""
    def __init__(self, block, atEnd=False):
        """Positions the token iterator at the start of the given block.
        
        If atEnd == True, the iterator is positioned past the end of the block.
        
        """
        self.block = block
        # if block is an empty line, the highlighter doesn't run
        self._tokens = block.userData().tokens if block.userData() and block.length() > 1 else ()
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
    
    def cursor(self):
        """Returns a QTextCursor for the last token."""
        token = self._tokens[self._index]
        cursor = QTextCursor(self.block)
        cursor.setPosition(self.block.position() + token.pos)
        cursor.setPosition(self.block.position() + token.end, QTextCursor.KeepAnchor)
        return cursor


