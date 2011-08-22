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
Highlighter for the snippet editor and view.
"""

import __builtin__
import keyword

from PyQt4.QtGui import QSyntaxHighlighter

import slexer

import app
import textformats

from . import snippets


class Highlighter(QSyntaxHighlighter):
    
    def __init__(self, document):
        super(Highlighter, self).__init__(document)
        self.python = None
        self._fridge = slexer.Fridge()
        self.readSettings()
        app.settingsChanged.connect(self.readSettingsAgain)
        
    def readSettings(self):
        self._styles = textformats.formatData('editor').defaultStyles
        
    def readSettingsAgain(self):
        self.readSettings()
        self.rehighlight()
        
    def setPython(self, python):
        """Force Python or generic snippet highlighting.
        
        Use True for Python, False for Snippet, or None to let the highlighter
        decide based on the variable lines.
        
        """
        if self.python is not python:
            self.python = python
            self.rehighlight()
    
    def highlightBlock(self, text):
        prev = self.previousBlockState()
        python = self.python if self.python is not None else prev == -2
        if text.startswith('-*- '):
            # the line defines variables, highlight them and check if 'python' is defined
            self.setFormat(0, 3, self._styles['keyword'])
            for m in snippets._variables_re.finditer(text):
                self.setFormat(m.start(1), m.end(1)-m.start(1), self._styles['variable'])
                if m.group(2):
                    self.setFormat(m.start(2), m.end(2)-m.start(2), self._styles['value'])
                python = python or m.group(1) == 'python'
            self.setCurrentBlockState(-2 if python else -1)
        else:
            # we are in the snippet text
            state = self._fridge.thaw(prev) or slexer.State(Python if python else Snippet)
            for t in state.tokens(text):
                if isinstance(t, String):
                    self.setFormat(t.pos, len(t), self._styles['string'])
                elif isinstance(t, Escape):
                    self.setFormat(t.pos, len(t), self._styles['escape'])
                elif isinstance(t, Comment):
                    self.setFormat(t.pos, len(t), self._styles['comment'])
                elif isinstance(t, Keyword):
                    self.setFormat(t.pos, len(t), self._styles['keyword'])
                elif isinstance(t, PyBuiltin):
                    self.setFormat(t.pos, len(t), self._styles['function'])
            self.setCurrentBlockState(self._fridge.freeze(state))


# Basic types:

class String(slexer.Token):
    pass

class Comment(slexer.Token):
    pass

class Escape(slexer.Token):
    pass

class Keyword(slexer.Token):
    pass


# Snippet types:

class StringStart(String):
    rx = '"'
    def updateState(self, state):
        state.enter(StringParser())

class StringEnd(StringStart):
    def updateState(self, state):
        state.leave()

class StringEscape(Escape):
    rx = r'\\["\\]'

class Expansion(Escape):
    rx = snippets._expansions_re.pattern
    
# Python types:

class PyKeyword(Keyword):
    rx = r"\b({0})\b".format('|'.join(keyword.kwlist))

class PyBuiltin(slexer.Token):
    rx = r"\b({0})\b".format('|'.join(__builtin__.__dict__.keys()))

class PyStringStartDQ1(String):
    rx = '[ub]?"'
    def updateState(self, state):
        state.enter(PyStringParserDQ1())

class PyStringStartDQ3(String):
    rx = '[ub]?"""'
    def updateState(self, state):
        state.enter(PyStringParserDQ3())

class PyStringStartSQ1(String):
    rx = "[ub]?'"
    def updateState(self, state):
        state.enter(PyStringParserSQ1())

class PyStringStartSQ3(String):
    rx = "[ub]?'''"
    def updateState(self, state):
        state.enter(PyStringParserSQ3())

class PyStringStartDQ1R(String):
    rx = '[ub]?r"'
    def updateState(self, state):
        state.enter(PyStringParserDQ1R())

class PyStringStartDQ3R(String):
    rx = '[ub]?r"""'
    def updateState(self, state):
        state.enter(PyStringParserDQ3R())

class PyStringStartSQ1R(String):
    rx = "[ub]?r'"
    def updateState(self, state):
        state.enter(PyStringParserSQ1R())

class PyStringStartSQ3R(String):
    rx = "[ub]?r'''"
    def updateState(self, state):
        state.enter(PyStringParserSQ3R())

class PyStringEndDQ1(StringEnd):
    rx = '"'

class PyStringEndDQ3(StringEnd):
    rx = '"""'

class PyStringEndSQ1(StringEnd):
    rx = "'"

class PyStringEndSQ3(StringEnd):
    rx = "'''"

class PyStringEscapeDQ(Escape):
    rx = r'\\["\\]'
    
class PyStringEscapeSQ(Escape):
    rx = r"\\['\\]"
    
class PyComment(Comment):
    rx = "#"
    def updateState(self, state):
        state.enter(PyCommentParser())

class NewlineEnd(slexer.Token):
    """Newline to leave context."""
    def updateState(self, state):
        state.leave()


# Parsers, many because of complicated string quote types in Python
class StringParser(slexer.Parser):
    default = String
    items = (
        StringEnd,
        StringEscape,
        Expansion,
    )

class Python(slexer.Parser):
    items = (
        PyKeyword,
        PyBuiltin,
        PyStringStartDQ3,
        PyStringStartDQ1,
        PyStringStartSQ3,
        PyStringStartSQ1,
        PyStringStartDQ3R,
        PyStringStartDQ1R,
        PyStringStartSQ3R,
        PyStringStartSQ1R,
        PyComment,
    )

class PyStringParserDQ1(StringParser):
    items = (
        PyStringEscapeDQ,
        PyStringEndDQ1,
    )

class PyStringParserDQ3(StringParser):
    items = (
        PyStringEscapeDQ,
        PyStringEndDQ3,
    )

class PyStringParserSQ1(StringParser):
    items = (
        PyStringEscapeSQ,
        PyStringEndSQ1,
    )

class PyStringParserSQ3(StringParser):
    items = (
        PyStringEscapeSQ,
        PyStringEndSQ3,
    )

class PyStringParserDQ1R(StringParser):
    items = (
        PyStringEndDQ1,
    )

class PyStringParserDQ3R(StringParser):
    items = (
        PyStringEndDQ3,
    )

class PyStringParserSQ1R(StringParser):
    items = (
        PyStringEndSQ1,
    )

class PyStringParserSQ3R(StringParser):
    items = (
        PyStringEndSQ3,
    )

class PyCommentParser(slexer.Parser):
    default = Comment
    items = (
        NewlineEnd,
    )

class Snippet(slexer.Parser):
    items = (
        StringStart,
        Expansion,
    )


