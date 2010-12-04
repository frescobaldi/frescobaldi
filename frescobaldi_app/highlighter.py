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
The Highlighter class provides syntax highlighting and more information
about a document's contents.
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *


import ly.tokenize


class Highlighter(QSyntaxHighlighter):
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        self.setDocument(document)
        self._states = []
        
    def highlightBlock(self, text):
        prev = self.previousBlockState()
        if 0 <= prev < len(self._states):
            state = ly.tokenize.State.thaw(self._states[prev])
        else:
            state = ly.tokenize.State(text)
        
        def setFormat(f): self.setFormat(token.pos, len(token), f)
        
        for token in ly.tokenize.tokens(text, state):
            if isinstance(token, ly.tokenize.lilypond.Command):
                setFormat(command)
            elif isinstance(token, ly.tokenize.html.EntityRef):
                setFormat(command)
            elif isinstance(token, ly.tokenize.EscapeBase):
                setFormat(escape)
            elif isinstance(token, ly.tokenize.StringBase):
                setFormat(string)
            elif isinstance(token, ly.tokenize.NumericBase):
                setFormat(value)
            elif isinstance(token, ly.tokenize.CommentBase):
                setFormat(comment)
                
                
        cur = state.freeze()
        try:
            self.setCurrentBlockState(self._states.index(cur))
        except ValueError:
            self.setCurrentBlockState(len(self._states))
            self._states.append(cur)


command = QTextCharFormat()
command.setFontWeight(QFont.Bold)
command.setForeground(QBrush(QColor(0, 0, 255)))

string = QTextCharFormat()
string.setForeground(QBrush(QColor(172, 0, 0)))

escape = QTextCharFormat()
escape.setFontWeight(QFont.Bold)
escape.setForeground(QBrush(QColor(255, 60, 60)))

value = QTextCharFormat()
value.setForeground(QBrush(QColor(220, 176, 57)))

comment = QTextCharFormat()
comment.setFontItalic(True)
comment.setForeground(QBrush(QColor(170, 170, 170)))
