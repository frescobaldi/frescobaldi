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
Parses and tokenizes Scheme input.
"""

from __future__ import unicode_literals

import _token
import _parser


class Scheme(_token.Token):
    """Baseclass for Scheme tokens."""
    pass


class String(_token.String):
    pass


class StringQuotedStart(String, _token.StringStart):
    rx = r'"'
    def changeState(self, state):
        state.enter(StringParser)
        

class StringQuotedEnd(String, _token.StringEnd):
    rx = r'"'
    def changeState(self, state):
        state.leave()
        state.endArgument()
    

class StringQuoteEscape(_token.Character):
    rx = r'\\[\\"]'


class Comment(_token.Comment):
    pass


class LineComment(Comment, _token.LineComment):
    rx = r";.*$"
    

class BlockCommentStart(Comment, _token.BlockCommentStart, _token.Indent):
    rx = r"#!"
    def changeState(self, state):
        state.enter(BlockCommentParser)
        

class BlockCommentEnd(Comment, _token.BlockCommentEnd, _token.Leaver, _token.Dedent):
    rx = "!#"


class BlockCommentSpace(Comment, _token.Space):
    pass


class OpenParen(Scheme, _token.MatchStart, _token.Indent):
    rx = r"\("
    matchname = "schemeparen"
    def changeState(self, state):
        state.enter(SchemeParser)


class CloseParen(Scheme, _token.MatchEnd, _token.Dedent):
    rx = r"\)"
    matchname = "schemeparen"
    def changeState(self, state):
        state.leave()
        state.endArgument()
        

class Quote(Scheme):
    rx = r"[',`]"
    

class Bool(Scheme, _token.Item):
    rx = r"#[tf]\b"
    

class Char(Scheme, _token.Item):
    rx = r"#\\([a-z]+|.)"


class Word(Scheme, _token.Item):
    rx = r'[^()"{}\s]+'


class Number(_token.Item, _token.Numeric):
    rx = r"-?\d+|#(b[0-1]+|o[0-7]+|x[0-9a-fA-F]+)"
    

class Fraction(Number):
    rx = r"-?\d+/\d+"


class Float(Number):
    rx = r"-?((\d+(\.\d*)|\.\d+)(E\d+)?)"


class LilyPond(_token.Token):
    pass


class LilyPondStart(LilyPond, _token.MatchStart, _token.Indent):
    rx = r"#{"
    matchname = "schemelily"
    def changeState(self, state):
        state.enter(LilyPondParser)
        

class LilyPondEnd(LilyPond, _token.Leaver, _token.MatchEnd, _token.Dedent):
    rx = r"#}"
    matchname = "schemelily"


# Parsers

class SchemeParser(_parser.Parser):
    mode = 'scheme'
    items = (
        _token.Space,
        OpenParen,
        CloseParen,
        LineComment,
        BlockCommentStart,
        LilyPondStart,
        Bool,
        Char,
        Quote,
        Fraction,
        Float,
        Number,
        Word,
        StringQuotedStart,
    )
    
    
class StringParser(_parser.Parser):
    default = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class BlockCommentParser(_parser.Parser):
    default = Comment
    items = (
        BlockCommentSpace,
        BlockCommentEnd,
    )


import lilypond

class LilyPondParser(lilypond.LilyPondParserMusic):
    items = (LilyPondEnd,) + lilypond.LilyPondParserMusic.items

