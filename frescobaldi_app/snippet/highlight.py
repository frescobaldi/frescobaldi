# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
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
Highlighter for the snippet editor and view.
"""


import builtins
import keyword

from PyQt5.QtGui import QSyntaxHighlighter

import app
import textformats
from ly import slexer

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
                if isinstance(t, Stylable):
                    self.setFormat(t.pos, len(t), self._styles[t.style])
            self.setCurrentBlockState(self._fridge.freeze(state))


# Basic types:
class Stylable(slexer.Token):
    """A token type with style ;-) to highlight."""
    style = '<set style here>'

class String(Stylable):
    style = 'string'

class Comment(Stylable):
    style = 'comment'

class Escape(Stylable):
    style = 'escape'

class Function(Stylable):
    style = 'function'

class Keyword(Stylable):
    style = 'keyword'

class Variable(Stylable):
    style = 'variable'

class Value(Stylable):
    style = 'value'


# Snippet types:

class StringStart(String):
    rx = '"'
    def update_state(self, state):
        state.enter(StringParser())

class StringEnd(StringStart):
    def update_state(self, state):
        state.leave()

class StringEscape(Escape):
    rx = r'\\["\\]'

class Expansion(Escape):
    rx = snippets._expansions_re.pattern

# Python types:

class PyKeyword(Keyword):
    rx = r"\b({0})\b".format('|'.join(keyword.kwlist))

class PyBuiltin(Function):
    rx = r"\b({0})\b".format('|'.join(builtins.__dict__))

class PyStringStartDQ1(String):
    rx = '[uUbB]?"'
    def update_state(self, state):
        state.enter(PyStringParserDQ1())

class PyStringStartDQ3(String):
    rx = '[uUbB]?"""'
    def update_state(self, state):
        state.enter(PyStringParserDQ3())

class PyStringStartSQ1(String):
    rx = "[uUbB]?'"
    def update_state(self, state):
        state.enter(PyStringParserSQ1())

class PyStringStartSQ3(String):
    rx = "[uUbB]?'''"
    def update_state(self, state):
        state.enter(PyStringParserSQ3())

class PyStringStartDQ1R(String):
    rx = '[uUbB]?[rR]"'
    def update_state(self, state):
        state.enter(PyStringParserDQ1R())

class PyStringStartDQ3R(String):
    rx = '[uUbB]?[rR]"""'
    def update_state(self, state):
        state.enter(PyStringParserDQ3R())

class PyStringStartSQ1R(String):
    rx = "[uUbB]?[rR]'"
    def update_state(self, state):
        state.enter(PyStringParserSQ1R())

class PyStringStartSQ3R(String):
    rx = "[uUbB]?[rR]'''"
    def update_state(self, state):
        state.enter(PyStringParserSQ3R())

class PyStringEndDQ1(StringEnd):
    rx = '"'

class PyStringEndDQ3(StringEnd):
    rx = '"""'

class PyStringEndSQ1(StringEnd):
    rx = "'"

class PyStringEndSQ3(StringEnd):
    rx = "'''"

class PyStringEscape(Escape):
    rx = (
        r"""\\([\\'"abfnrtv]"""
        r'|[0-7]{3}|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}'
        r'|N\{[A-Z]+( [A-Z]+)*\})'
    )

class PyStringEscapedNewline(Escape):
    """Highlights escaped newline."""
    rx = r'\\$'

class PyStringDoubleBackslashAtLineEnd(PyStringEscape):
    """Use this to leave a string at line end. Prevents staying in PyStringEOL."""
    rx = r'\\\\$'
    def update_state(self, state):
        state.leave()

class PyStringDoubleBackslashAtLineEndR(String):
    """Use this to leave a string at line end in raw. Prevents staying in PyStringEOL."""
    rx = r'\\\\$'
    def update_state(self, state):
        state.leave()

class PyStringEOL(slexer.Token):
    """Leaves a string at unescaped Newline."""
    rx = r'(?<!\\)$'
    def update_state(self, state):
        state.leave()

class PyComment(Comment):
    rx = "#"
    def update_state(self, state):
        state.enter(PyCommentParser())

class LineEnd(slexer.Token):
    """Newline to leave context."""
    rx = r'$'
    def update_state(self, state):
        state.leave()

class PyIdentifier(slexer.Token):
    rx = r"\b[^\W\d]\w+"

class PySpecialVariable(Variable):
    rx = r"\b(self|state|cursor|text|view|ANCHOR|CURSOR)\b"

class PyValue(Value):
    rx = (
        r"(0[bB][01]+|0[oO][0-7]+|0[xX][0-9A-Fa-f]+|\d+)[lL]?"
        r"|(\d+\.\d*|\.\d+)([eE][+-]?\d+)?"
    )

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
        PySpecialVariable,
        PyIdentifier,
        PyValue,
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
    """Parses string with one double quote."""
    items = (
        PyStringDoubleBackslashAtLineEnd,
        PyStringEscape,
        PyStringEscapedNewline,
        PyStringEOL,
        PyStringEndDQ1,
    )

class PyStringParserDQ3(StringParser):
    """Parses string with three double quotes."""
    items = (
        PyStringEscape,
        PyStringEscapedNewline,
        PyStringEndDQ3,
    )

class PyStringParserSQ1(StringParser):
    """Parses string with one single quote."""
    items = (
        PyStringDoubleBackslashAtLineEnd,
        PyStringEscape,
        PyStringEscapedNewline,
        PyStringEOL,
        PyStringEndSQ1,
    )

class PyStringParserSQ3(StringParser):
    """Parses string with three single quotes."""
    items = (
        PyStringEscape,
        PyStringEscapedNewline,
        PyStringEndSQ3,
    )

class PyStringParserDQ1R(StringParser):
    """Parses raw string with one double quote."""
    items = (
        PyStringDoubleBackslashAtLineEndR,
        PyStringEscapedNewline,
        PyStringEOL,
        PyStringEndDQ1,
    )

class PyStringParserDQ3R(StringParser):
    """Parses raw string with three double quotes."""
    items = (
        PyStringEscapedNewline,
        PyStringEndDQ3,
    )

class PyStringParserSQ1R(StringParser):
    """Parses raw string with one single quote."""
    items = (
        PyStringDoubleBackslashAtLineEndR,
        PyStringEscapedNewline,
        PyStringEOL,
        PyStringEndSQ1,
    )

class PyStringParserSQ3R(StringParser):
    """Parses raw string with three single quotes."""
    items = (
        PyStringEscapedNewline,
        PyStringEndSQ3,
    )

class PyCommentParser(slexer.Parser):
    """Parses comment."""
    default = Comment
    items = (
        LineEnd,
    )

class Snippet(slexer.Parser):
    """Just parses simple double-quoted string and dollar-sign expansions."""
    items = (
        StringStart,
        Expansion,
    )


