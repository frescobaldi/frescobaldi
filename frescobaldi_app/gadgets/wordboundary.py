# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
Provides custom word-boundary behaviour for QTextCursor and QTextEdit etc.

You can inherit from BoundaryHandler to change the behaviour. You can just
change the word_regexp expression, or override the boundaries() method.

Install a BoundaryHandler as eventfilter on a QTextEdit or QPlainTextEdit.
If you also want the double-click word selection to work, install the handler
also as eventfilter on the textedit's viewport(). The install_textedit() and
remove_textedit() methods can do this.

The handler intercepts the word-related cursor movement and selection
keypress events.

It is enough to have one global handler object, it can be installed on as
many textedit widgets as you like.

"""


import itertools
import operator
import re
import time

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QKeySequence, QTextCursor
from PyQt5.QtWidgets import QApplication


_move_operations = (
    QTextCursor.StartOfWord,
    QTextCursor.PreviousWord,
    QTextCursor.WordLeft,
    QTextCursor.EndOfWord,
    QTextCursor.NextWord,
    QTextCursor.WordRight,
)


class BoundaryHandler(QObject):

    _double_click_time = 0.0
    word_regexp = re.compile(r'\\?\w+|^|$', re.UNICODE)

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

        Other move operations are delegated to the QTextCursor itself.
        """
        block = cursor.block()
        pos = cursor.position() - block.position()
        if operation == QTextCursor.StartOfWord:
            if pos:
                for start, end in reversed(self.boundaries(block)):
                    if start < pos:
                        if end < pos:
                            return False
                        cursor.setPosition(block.position() + start, mode)
                        return True
            return False
        elif operation == QTextCursor.EndOfWord:
            for start, end in self.boundaries(block):
                if end > pos:
                    if start > pos:
                        return False
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

        Other selection types are delegated to the QTextCursor itself.

        """
        if selection == QTextCursor.WordUnderCursor:
            self.move(cursor, QTextCursor.StartOfWord)
            self.move(cursor, QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
        else:
            cursor.select(selection)

    def install_textedit(self, edit):
        """Install ourselves as event filter on the textedit and its viewport."""
        edit.installEventFilter(self)
        edit.viewport().installEventFilter(self)

    def remove_textedit(self, edit):
        """Remove ourselves as event filter from the textedit and its viewport."""
        edit.removeEventFilter(self)
        edit.viewport().removeEventFilter(self)

    def get_textedit(self, obj):
        """Return the textedit widget if obj is its viewport.

        If obj is not the viewport of its parent, obj itself is returned.

        """
        parent = obj.parent()
        try:
            if obj is parent.viewport():
                return parent
        except AttributeError:
            pass
        return obj

    def eventFilter(self, obj, ev):
        """Intercept key events from a Q(Plain)TextEdit and handle them."""
        if ev.type() == QEvent.KeyPress:
            return self.keyPressEvent(obj, ev)
        elif ev.type() == QEvent.MouseButtonDblClick:
            edit = self.get_textedit(obj)
            return self.mouseDoubleClickEvent(edit, ev)
        return False

    def keyPressEvent(self, obj, ev):
        """Handles the Word-related key events for the Q(Plain)TextEdit."""
        c = obj.textCursor()
        if ev == QKeySequence.DeleteEndOfWord:
            self.move(c, QTextCursor.NextWord, QTextCursor.KeepAnchor)
            c.removeSelectedText()
        elif ev == QKeySequence.DeleteStartOfWord:
            self.move(c, QTextCursor.PreviousWord, QTextCursor.KeepAnchor)
            c.removeSelectedText()
        elif ev == QKeySequence.MoveToNextWord:
            self.move(c, QTextCursor.NextWord)
            obj.setTextCursor(c)
        elif ev == QKeySequence.MoveToPreviousWord:
            self.move(c, QTextCursor.PreviousWord)
            obj.setTextCursor(c)
        elif ev == QKeySequence.SelectNextWord:
            self.move(c, QTextCursor.NextWord, QTextCursor.KeepAnchor)
            obj.setTextCursor(c)
        elif ev == QKeySequence.SelectPreviousWord:
            self.move(c, QTextCursor.PreviousWord, QTextCursor.KeepAnchor)
            obj.setTextCursor(c)
        else:
            return False
        return True

    def mouseDoubleClickEvent(self, obj, ev):
        """Handles the double-click even to select a word."""
        if ev.button() == Qt.LeftButton:
            block = obj.blockSignals(True) # prevent selectionChanged etc emitted twice
            obj.mouseDoubleClickEvent(ev)  # otherwise triple click and drag won't work
            obj.blockSignals(block)
            c = obj.cursorForPosition(ev.pos())
            self.select(c, QTextCursor.WordUnderCursor)
            obj.setTextCursor(c)
            return True
        return False


