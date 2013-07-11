# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
    

class BlockCommentStart(Comment, _token.BlockCommentStart, _token.Indent):
    rx = r"#!"
    def update_state(self, state):
        state.enter(ParseBlockComment())
        

class BlockCommentEnd(Comment, _token.BlockCommentEnd, _token.Leaver, _token.Dedent):
    rx = "!#"


class BlockCommentSpace(Comment, _token.Space):
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
    rx = r"'"
    def update_state(self, state):
        state.enter(ParseSchemeSymbol())
    
    
class Bool(Scheme, _token.Item):
    rx = r"#[tf]\b"
    
    
class Char(Scheme, _token.Item):
    rx = r"#\\([a-z]+|.)"


class Word(Scheme, _token.Item):
    rx = r'[^()"{}\s]+'


class Keyword(Scheme):
    @_token.patternproperty
    def rx():
        from .. import data
        import re
        lst = re.sub(r'([\?\*\+])', r"\\\1", 
                     "|".join(sorted(data.scheme_keywords(), key=len, reverse=True)))
        return r"({0})(?![A-Za-z-])".format(lst)
    
class Function(Word):
    @_token.patternproperty
    def rx():
        from .. import data
        import re
        lst = re.sub(r'([\?\*\+])', r"\\\1", 
                     "|".join(sorted(data.scheme_functions(), key=len, reverse=True)))
        return r"({0})(?![A-Za-z-])".format(lst)
    
class Variable(Word):
    @_token.patternproperty
    def rx():
        from .. import data
        import re
        lst = re.sub(r'([\?\*\+])', r"\\\1", 
                     "|".join(sorted(data.scheme_variables(), key=len, reverse=True)))
        return r"({0})(?![A-Za-z-])".format(lst)
    
    
class Constant(Word):
    @_token.patternproperty
    def rx():
        from .. import data
        import re
        lst = re.sub(r'([\?\*\+])', r"\\\1", 
                     "|".join(sorted(data.scheme_constants(), key=len, reverse=True)))
        return r"({0})(?![A-Za-z-])".format(lst)
    
class Symbol(Word):
    rx = r"[a-zA-Z-]+(?![a-zA-Z])"
    def update_state(self, state):
        state.leave()
        state.endArgument()
    

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
        Bool,
        Char,
        Quote,
        Fraction,
        Keyword,
        Function,
        Variable,
        Constant,
        Float,
        Number,
        Word,
        StringQuotedStart,
    )
    

class ParseSchemeSymbol(FallthroughParser):
    mode = 'scheme'
    items = (Symbol,)
   
class ParseString(Parser):
    default = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class ParseBlockComment(Parser):
    default = Comment
    items = (
        BlockCommentSpace,
        BlockCommentEnd,
    )


import lilypond

class ParseLilyPond(lilypond.ParseMusic):
    items = (LilyPondEnd,) + lilypond.ParseMusic.items

