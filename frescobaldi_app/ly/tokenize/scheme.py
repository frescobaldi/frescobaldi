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
Parses and tokenizes Scheme input.
"""

from . import (
    Parser,
    Token,
    Item,
    Space,
    Increaser,
    Decreaser,
    Leaver,
    NumericBase,
    CommentBase,
    StringBase,
    EscapeBase,
    StringParserBase,
)


class Scheme(Token):
    """Baseclass for Scheme tokens."""
    pass


class String(StringBase):
    pass


class StringQuotedStart(String):
    rx = r'"'
    def __init__(self, matchObj, state):
        state.enter(StringParser)
        

class StringQuotedEnd(String):
    rx = r'"'
    def __init__(self, matchObj, state):
        state.leave()
        state.endArgument()
    

class StringQuoteEscape(String, EscapeBase):
    rx = r'\\[\\"]'


class Comment(CommentBase):
    pass


class LineComment(Comment):
    rx = r";.*$"
    

class BlockCommentStart(Comment):
    rx = r"#!"
    def __init__(self, matchObj, state):
        state.enter(BlockCommentParser)
        

class BlockCommentEnd(Comment, Leaver):
    rx = "!#"


class OpenParen(Scheme, Increaser):
    rx = r"\("
    

class CloseParen(Scheme, Decreaser):
    rx = r"\)"


class Quote(Scheme):
    rx = r"[',`]"
    

class Bool(Scheme, Item):
    rx = r"#[tf]\b"
    

class Char(Scheme, Item):
    rx = r"#\\([a-z]+|.)"


class Word(Scheme, Item):
    rx = r'[^()"{}\s]+'


class Number(Item, NumericBase):
    rx = r"-?\d+|#(b[0-1]+|o[0-7]+|x[0-9a-fA-F]+)"
    

class Fraction(Number):
    rx = r"-?\d+/\d+"


class Float(Number):
    rx = r"-?\d+E\d+|\d+\.\d*|\d*\.\d+"


class LilyPond(Token):
    pass


class LilyPondStart(LilyPond):
    rx = r"#{"
    def __init__(self, matchObj, state):
        state.enter(LilyPondParser)
        

class LilyPondEnd(LilyPond, Leaver):
    rx = r"#}"
    

# Parsers

class SchemeParser(Parser):
    argcount = 1
    items = (
        Space,
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
    
    
class StringParser(StringParserBase):
    defaultClass = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class BlockCommentParser(Parser):
    defaultClass = Comment
    items = (
        BlockCommentEnd,
    )


import lilypond

class LilyPondParser(lilypond.LilyPondParser):
    items = (LilyPondEnd,) + lilypond.LilyPondParser.items

