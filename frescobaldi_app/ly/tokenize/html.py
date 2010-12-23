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
Parses and tokenizes HTML input, recognizing LilyPond in HTML.
"""

from . import (
    Token,
    Space,
    Leaver,
    StringBase,
    CommentBase,
    Parser,
    FallthroughParser,
    StringParserBase,
)

import lilypond


class Comment(CommentBase):
    pass


class CommentStart(Comment):
    rx = r"<!--"
    def changeState(self, state):
        state.enter(CommentParser)
        
        
class CommentEnd(Comment, Leaver):
    rx = r"-->"


class String(StringBase):
    pass


class Tag(Token):
    pass


class TagStart(Tag):
    rx = r"</?\w[-_:\w]*\b"
    def changeState(self, state):
        state.enter(AttrParser)
        

class TagEnd(Tag, Leaver):
    rx = r"/?>"
    

class AttrName(Token):
    rx = r"\w+([-_:]\w+)?"
    
    
class EqualSign(Token):
    rx = "="
    def changeState(self, state):
        state.enter(ValueParser)


class Value(Leaver):
    rx = r"\w+"
    

class StringDQStart(String):
    rx = r'"'
    def changeState(self, state):
        state.enter(StringDQParser)


class StringSQStart(String):
    rx = r"'"
    def changeState(self, state):
        state.enter(StringSQParser)
    

class StringEnd(String, Leaver):
    pass


class StringDQEnd(StringEnd):
    rx = r'"'
    

class StringSQEnd(StringEnd):
    rx = r"'"


class EntityRef(Token):
    rx = r"\&(#\d+|#[xX][0-9A-Fa-f]+|[A-Za-z_:][\w.:_-]*);"


class LilyPondTag(Tag):
    pass


class LilyPondVersionTag(LilyPondTag):
    rx = r"<lilypondversion/?>"


class LilyPondFileTag(LilyPondTag):
    rx = r"</?lilypondfile\b"
    def changeState(self, state):
        state.enter(LilyPondFileOptionsParser)


class LilyPondFileTagEnd(LilyPondTag, Leaver):
    rx = r"/?>"


class LilyPondInlineTag(LilyPondTag):
    rx = r"<lilypond\b"
    def changeState(self, state):
        state.enter(LilyPondAttrParser)


class LilyPondCloseTag(LilyPondTag, Leaver):
    rx = r"</lilypond>"
    
    
class LilyPondTagEnd(LilyPondTag):
    rx = r">"
    def changeState(self, state):
        state.replace(LilyPondParser)


class LilyPondInlineTagEnd(LilyPondTag, Leaver):
    rx = r"/?>"
    

class SemiColon(Token):
    rx = r":"
    def changeState(self, state):
        state.replace(LilyPondInlineParser)



# Parsers:

class HTMLParser(Parser):
    items = (
        Space,
        LilyPondVersionTag,
        LilyPondFileTag,
        LilyPondInlineTag,
        CommentStart,
        TagStart,
        EntityRef,
    )


class AttrParser(Parser):
    items = (
        Space,
        TagEnd,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
    )


class StringDQParser(StringParserBase):
    default = String
    items = (
        StringDQEnd,
        EntityRef,
    )
    

class StringSQParser(StringParserBase):
    default = String
    items = (
        StringSQEnd,
        EntityRef,
    )
    

class CommentParser(Parser):
    default = Comment
    items = (
        CommentEnd,
    )


class ValueParser(FallthroughParser):
    """Finds a value or drops back."""
    items = (
        Space,
        Value,
    )
    def fallthrough(self, state):
        state.leave()


class LilyPondAttrParser(Parser):
    items = (
        Space,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
        LilyPondTagEnd,
        SemiColon,
    )
    

class LilyPondFileOptionsParser(Parser):
    items = (
        Space,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
        LilyPondFileTagEnd,
    )


class LilyPondParser(lilypond.LilyPondParserGlobal):
    items = (
        LilyPondCloseTag,
    ) + lilypond.LilyPondParserGlobal.items
    

class LilyPondInlineParser(lilypond.LilyPondParserMusic):
    items = (
        LilyPondInlineTagEnd,
    ) + lilypond.LilyPondParserMusic.items
    

