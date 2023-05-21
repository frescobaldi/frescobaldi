# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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
Parses and tokenizes MUP input.

MUP (www.arkkra.com) is an open source music typesetter (formerly shareware).

We add a tokenizer here, to enable a decent mup2ly conversion.

"""

from __future__ import unicode_literals


from . import _token
from . import Parser, FallthroughParser


class Comment(_token.Comment):
    pass


class LineComment(Comment):
    rx = r"//.*$"


class String(_token.String):
    pass


class StringQuotedStart(String, _token.StringStart):
    rx = r'"'
    def update_state(self, state):
        state.enter(ParseString())
        

class StringQuotedEnd(String, _token.StringEnd):
    rx = r'"'
    def update_state(self, state):
        state.leave()
        state.endArgument()


class StringQuoteEscape(_token.Character):
    rx = r'\\[\\"]'


class Macro(_token.Token):
    rx = r'\b[A-Z][A-Z0-9_]*'


class Preprocessor(_token.Token):
    rx = (r'\b('
        'if|then|else|endif|define|undef|ifdef|ifndef'
        r')\b|@')


class ParseMup(Parser):
    mode = "mup"
    items = (
        LineComment,
        StringQuotedStart,
        Macro,
        Preprocessor,
    )


class ParseString(Parser):
    default = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )

