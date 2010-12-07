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
Parses and tokenizes LilyPond input.
"""

from . import (
    Token,
    Item,
    Leaver,
    Space,
    
    CommentBase,
    StringBase,
    EscapeBase,
    Parser,
    StringParserBase,
)


class Comment(CommentBase):
    pass


class BlockCommentStart(Comment):
    rx = r"%{"
    def __init__(self, matchObj, state):
        state.enter(BlockCommentParser)


class BlockCommentEnd(Comment, Leaver):
    rx = r"%}"


class LineComment(Comment):
    rx = r"%.*$"
    

class Command(Token):
    rx = r"\\[a-zA-Z]+"
    

class Scheme(Token):
    rx = "#"
    def __init__(self, matchObj, state):
        import scheme
        state.enter(scheme.SchemeParser)


class String(StringBase):
    pass


class StringQuoted(String, Item):
    rx = r'"(\\[\\"]|[^"\n\\]|\\(?![\\"]))*"'
    

class StringQuotedStart(String):
    rx = r'"'
    def __init__(self, matchObj, state):
        state.enter(StringParser)
        

class StringQuotedEnd(String, Leaver):
    rx = r'"'
    

class StringQuoteEscape(String, EscapeBase):
    rx = r'\\[\\"]'


class LilyPondParser(Parser):
    items = (
        Space,
        BlockCommentStart,
        LineComment,
        Scheme,
        StringQuoted,
        StringQuotedStart,
        Command,
    )
    

class StringParser(StringParserBase):
    defaultClass = String
    argcount = 1
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class BlockCommentParser(Parser):
    defaultClass = Comment
    items = (
        BlockCommentEnd,
    )

