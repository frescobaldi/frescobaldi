# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
Provides better word-boundary behaviour for QTextCursor and QTextEdit etc.
"""

from __future__ import unicode_literals

import itertools
import operator
import re

from PyQt4.QtGui import QTextCursor


_move_operations = (
    QTextCursor.StartOfWord,
    QTextCursor.PreviousWord,
    QTextCursor.WordLeft,
    QTextCursor.EndOfWord,
    QTextCursor.NextWord,
    QTextCursor.WordRight,
)


class BoundaryHandler(object):
    
    word_regexp = re.compile(r'\\?\w+')
    
    def boundaries(self, block):
        """Return a list of tuples specifying the position of words in the block.
        
        Each tuple denotes the start and end position of a "word" in the
        specified block.
        
        You can return other boundaries by changing the word_regexp or by
        inheriting from this class and overwriting this method.
        
        """
        return [m.span() for m in self.word_regexp.finditer(block.text())]
    
    def left_boundaries(self, block):
        left = operator.itemgetter(0)
        return [left(b) for b in self.boundaries(block)]
        
    def right_boundaries(self, block):
        right = operator.itemgetter(1)
        return [right(b) for b in self.boundaries(block)]
        
    def move(self, cursor, operation, mode=QTextCursor.MoveAnchor, n=1):
        """Reimplements Word-related cursor operations:
        
        StartOfWord
        PreviousWord
        WordLeft
        EndOfWord
        NextWord
        WordRight
        
        Other move operations are delegated to the QTextCursor ifself.
        """
        block = cursor.block()
        pos = cursor.position() - block.position()
        if operation == QTextCursor.StartOfWord:
            if pos:
                for start in reversed(self.left_boundaries(block)):
                    if start == pos:
                        return False
                    elif start < pos:
                        cursor.setPosition(block.position() + start, mode)
                        return True
            return False
        elif operation == QTextCursor.EndOfWord:
            for end in self.right_boundaries(block):
                if end == pos:
                    return False
                elif end > pos:
                    cursor.setPosition(block.position() + end, mode)
                    return True
            return False
        elif operation in (QTextCursor.PreviousWord, QTextCursor.WordLeft):
            boundaries = list(itertools.takewhile(lambda b: b<pos, self.left_boundaries(block)))
            while True:
                if len(boundaries) >= n:
                    cursor.setPosition(block.position() + boundaries[-n], mode)
                    return True
                n -= len(boundaries)
                block = block.previous()
                if not block.isValid():
                    cursor.setPosition(0, mode)
                    return False
                boundaries = self.left_boundaries(block)
        elif operation in (QTextCursor.NextWord, QTextCursor.WordRight):
            boundaries = list(itertools.dropwhile(lambda b: b<=pos, self.left_boundaries(block)))
            while True:
                if len(boundaries) >= n:
                    cursor.setPosition(block.position() + boundaries[n-1], mode)
                    return True
                n -= len(boundaries)
                block = block.next()
                if not block.isValid():
                    cursor.movePosition(QTextCursor.End, mode)
                    return False
                boundaries = self.left_boundaries(block)
        else:
            return cursor.movePosition(operation, mode, n)
        
    def select(self, cursor, selection):
        """Reimplements the WordUnderCursor selection type.
        
        Other selection types are delegated to the QTextCursor ifself.
        
        """
        if selection != QTextCursor.WordUnderCursor:
            return cursor.select(selection)
        self.move(cursor, QTextCursor.StartOfWord)
        cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        self.move(cursor, QTextCursor.EndOfWord, QTextCursor.KeepAnchor)


