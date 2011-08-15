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
A basic parenthesis/brace character matcher for a textedit widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Matcher(QObject):
    
    # These attributes may be overridden by setting them as instance attributes
    
    # should be a string of characters that match in pairs with each other
    matchPairs = "{}()[]"
    
    # a QTextCharFormat to highlight the matching characters with
    format = QTextCharFormat()
    format.setForeground(Qt.red)
    
    # how long the highlighting is shown in msec
    time = 2000
    
    def __init__(self, edit):
        super(Matcher, self).__init__(edit)
        self._timer = QTimer(singleShot=True, timeout=self.clearHighlight)
        edit.cursorPositionChanged.connect(self.slotCursorPositionChanged)
    
    def edit(self):
        """Returns our Q(Plain)TextEdit."""
        return self.parent()
    
    def slotCursorPositionChanged(self):
        """Called whenever the cursor position changes.
        
        Highlights matching characters if the cursor is at one of them.
        
        """
        cursor = self.edit().textCursor()
        block = cursor.block()
        text = block.text()
        
        # try both characters at the cursor
        col = cursor.position() - block.position()
        end = col + 1
        col = max(0, col - 1)
        for c in text[col:end]:
            if c in self.matchPairs:
                break
            col += 1
        else:
            self.clearHighlight()
            return
        
        # the cursor is at a character from matchPairs
        i = self.matchPairs.index(c)
        cursor.setPosition(block.position() + col)
        
        # find the matching character
        new = QTextCursor(cursor)
        if i & 1:
            # look backward
            match = self.matchPairs[i-1]
            flags = QTextDocument.FindBackward
        else:
            # look forward
            match = self.matchPairs[i+1]
            flags = QTextDocument.FindFlags()
            new.movePosition(QTextCursor.Right)
        
        # search, also nesting
        rx = QRegExp(QRegExp.escape(c) + '|' + QRegExp.escape(match))
        nest = 0
        while nest >= 0:
            new = cursor.document().find(rx, new, flags)
            if new.isNull():
                self.clearHighlight()
                return
            nest += 1 if new.selectedText() == c else -1
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        self.highlight([cursor, new])
    
    def highlight(self, cursors):
        selections = []
        for cursor in cursors:
            es = QTextEdit.ExtraSelection()
            es.cursor = cursor
            es.format = self.format
            selections.append(es)
        self.edit().setExtraSelections(selections)
        if selections:
            self._timer.start(self.time)
    
    def clearHighlight(self):
        self.edit().setExtraSelections([])
        
    