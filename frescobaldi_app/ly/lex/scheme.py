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
Parses and tokenizes Scheme input.
"""

from __future__ import unicode_literals

from . import _token
from . import Parser, FallthroughParser


class Scheme(_token.Token):
    """Baseclass for Scheme tokens."""
    pass


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


class Comment(_token.Comment):
    pass


class LineComment(Comment, _token.LineComment):
    rx = r";.*$"
    

class BlockCommentStart(Comment, _token.BlockCommentStart):
    rx = r"#!"
    def update_state(self, state):
        state.enter(ParseBlockComment())
        

class BlockCommentEnd(Comment, _token.BlockCommentEnd, _token.Leaver):
    rx = "!#"


class BlockComment(Comment, _token.BlockComment):
    pass


class OpenParen(Scheme, _token.MatchStart, _token.Indent):
    rx = r"\("
    matchname = "schemeparen"
    def update_state(self, state):
        state.enter(ParseScheme())


class CloseParen(Scheme, _token.MatchEnd, _token.Dedent):
    rx = r"\)"
    matchname = "schemeparen"
    def update_state(self, state):
        state.leave()
        state.endArgument()
        

class Quote(Scheme):
    rx = r"['`,]"
    
    
class Dot(Scheme):
    rx = r"\.(?!\S)"


class Bool(Scheme, _token.Item):
    rx = r"#[tf]\b"
    
    
class Char(Scheme, _token.Item):
    rx = r"#\\([a-z]+|.)"


class Word(Scheme, _token.Item):
    rx = r'[^()"{}\s]+'


class Keyword(Word):
    @classmethod
    def test_match(cls, match):
        from .. import data
        return match.group() in data.scheme_keywords()


class Function(Word):
    @classmethod
    def test_match(cls, match):
        from .. import data
        return match.group() in data.scheme_functions()


class Variable(Word):
    @classmethod
    def test_match(cls, match):
        from .. import data
        return match.group() in data.scheme_variables()


class Constant(Word):
    @classmethod
    def test_match(cls, match):
        from .. import data
        return match.group() in data.scheme_constants()


class Number(_token.Item, _token.Numeric):
    rx = (r"("
          r"-?\d+|"
          r"#(b[0-1]+|o[0-7]+|x[0-9a-fA-F]+)|"
          r"[-+]inf.0|[-+]?nan.0"
          r")(?=$|[)\s])")


class Fraction(Number):
    rx = r"-?\d+/\d+(?=$|[)\s])"


class Float(Number):
    rx = r"-?((\d+(\.\d*)|\.\d+)(E\d+)?)(?=$|[)\s])"


class LilyPond(_token.Token):
    pass


class LilyPondStart(LilyPond, _token.MatchStart, _token.Indent):
    rx = r"#{"
    matchname = "schemelily"
    def update_state(self, state):
        state.enter(ParseLilyPond())
        

class LilyPondEnd(LilyPond, _token.Leaver, _token.MatchEnd, _token.Dedent):
    rx = r"#}"
    matchname = "schemelily"


# Parsers

class ParseScheme(Parser):
    mode = 'scheme'
    items = (
        _token.Space,
        OpenParen,
        CloseParen,
        LineComment,
        BlockCommentStart,
        LilyPondStart,
        Dot,
        Bool,
        Char,
        Quote,
        Fraction,
        Float,
        Number,
        Constant,
        Keyword,
        Function,
        Variable,
        Word,
        StringQuotedStart,
    )
    

class ParseString(Parser):
    default = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class ParseBlockComment(Parser):
    default = BlockComment
    items = (
        BlockCommentEnd,
    )


from . import lilypond

class ParseLilyPond(lilypond.ParseMusic):
    items = (LilyPondEnd,) + lilypond.ParseMusic.items

