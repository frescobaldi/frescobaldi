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
    Increaser,
    Decreaser,
    Space,
    
    CommentBase,
    StringBase,
    EscapeBase,
    Parser,
    StringParserBase,
)

from .. import words


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
    

class Delimiter(Token):
    pass


class OpenBracket(Delimiter, Increaser):
    rx = r"\{"


class CloseBracket(Delimiter, Decreaser):
    rx = r"\}"


class Keyword(Item):
    rx = r"\\({0})\b".format("|".join(words.lilypond_keywords))


class Command(Item):
    rx = r"\\({0})\b".format("|".join(words.lilypond_music_commands))
    

class Markup(Command):
    rx = r"\\markup\b"
    def __init__(self, matchObj, state):
        state.enter(MarkupParser)


class MarkupLines(Markup):
    rx = r"\\markuplines\b"
    def __init__(self, matchObj, state):
        state.enter(MarkupParser)


class MarkupCommand(Markup):
    rx = r"\\[A-Za-z]+(-[A-Za-z]+)*"
    def __init__(self, matchObj, state):
        command = self[1:]
        if command in words.markupcommands_nargs[0]:
            state.endArgument()
        else:
            for argcount in 2, 3, 4:
                if command in words.markupcommands_nargs[argcount]:
                    break
            else:
                argcount = 1
            state.enter(MarkupParser, argcount)


class UserCommand(Token):
    rx = r"\\[A-Za-z]+"
    
    
class String(StringBase):
    pass


class StringQuotedStart(String):
    rx = r'"'
    def __init__(self, matchObj, state):
        state.enter(StringParser)
        

class StringQuotedEnd(String, Leaver):
    rx = r'"'
    

class StringQuoteEscape(String, EscapeBase):
    rx = r'\\[\\"]'


class SchemeStart(Item):
    rx = "#"
    def __init__(self, matchObj, state):
        import scheme
        state.enter(scheme.SchemeParser)


# Parsers

class LilyPondParser(Parser):
    items = (
        Space,
        BlockCommentStart,
        LineComment,
        SchemeStart,
        StringQuotedStart,
        Keyword,
        Markup,
        MarkupLines,
        Command,
        UserCommand,
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


class MarkupParser(Parser):
    argcount = 1
    items =  (
#        MarkupScore,
        MarkupCommand,
        OpenBracket,
        CloseBracket,
    ) + LilyPondParser.items
