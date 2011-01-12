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

import _token as token
import _parser as parser

import lilypond


class Comment(token.Comment):
    pass


class CommentStart(Comment, token.BlockCommentStart):
    rx = r"<!--"
    def changeState(self, state):
        state.enter(CommentParser)
        
        
class CommentEnd(Comment, token.Leaver, token.BlockCommentEnd):
    rx = r"-->"


class String(token.String):
    pass


class Tag(token.Token):
    pass


class TagStart(Tag):
    rx = r"</?\w[-_:\w]*\b"
    def changeState(self, state):
        state.enter(AttrParser)
        

class TagEnd(Tag, token.Leaver):
    rx = r"/?>"
    

class AttrName(token.Token):
    rx = r"\w+([-_:]\w+)?"
    
    
class EqualSign(token.Token):
    rx = "="
    def changeState(self, state):
        state.enter(ValueParser)


class Value(token.Leaver):
    rx = r"\w+"
    

class StringDQStart(String, token.StringStart):
    rx = r'"'
    def changeState(self, state):
        state.enter(StringDQParser)


class StringSQStart(String, token.StringStart):
    rx = r"'"
    def changeState(self, state):
        state.enter(StringSQParser)
    

class StringDQEnd(String, token.StringEnd):
    rx = r'"'
    

class StringSQEnd(String, token.StringEnd):
    rx = r"'"


class EntityRef(token.Character):
    rx = r"\&(#\d+|#[xX][0-9A-Fa-f]+|[A-Za-z_:][\w.:_-]*);"


class LilyPondTag(Tag):
    pass


class LilyPondVersionTag(LilyPondTag):
    rx = r"<lilypondversion/?>"


class LilyPondFileTag(LilyPondTag):
    rx = r"</?lilypondfile\b"
    def changeState(self, state):
        state.enter(LilyPondFileOptionsParser)


class LilyPondFileTagEnd(LilyPondTag, token.Leaver):
    rx = r"/?>"


class LilyPondInlineTag(LilyPondTag):
    rx = r"<lilypond\b"
    def changeState(self, state):
        state.enter(LilyPondAttrParser)


class LilyPondCloseTag(LilyPondTag, token.Leaver):
    rx = r"</lilypond>"
    
    
class LilyPondTagEnd(LilyPondTag):
    rx = r">"
    def changeState(self, state):
        state.replace(LilyPondParser)


class LilyPondInlineTagEnd(LilyPondTag, token.Leaver):
    rx = r"/?>"
    

class SemiColon(token.Token):
    rx = r":"
    def changeState(self, state):
        state.replace(LilyPondInlineParser)



# Parsers:

class HTMLParser(parser.Parser):
    items = (
        token.Space,
        LilyPondVersionTag,
        LilyPondFileTag,
        LilyPondInlineTag,
        CommentStart,
        TagStart,
        EntityRef,
    )


class AttrParser(parser.Parser):
    items = (
        token.Space,
        TagEnd,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
    )


class StringDQParser(parser.Parser):
    default = String
    items = (
        StringDQEnd,
        EntityRef,
    )
    

class StringSQParser(parser.Parser):
    default = String
    items = (
        StringSQEnd,
        EntityRef,
    )
    

class CommentParser(parser.Parser):
    default = Comment
    items = (
        CommentEnd,
    )


class ValueParser(parser.FallthroughParser):
    """Finds a value or drops back."""
    items = (
        token.Space,
        Value,
    )
    def fallthrough(self, state):
        state.leave()


class LilyPondAttrParser(parser.Parser):
    items = (
        token.Space,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
        LilyPondTagEnd,
        SemiColon,
    )
    

class LilyPondFileOptionsParser(parser.Parser):
    items = (
        token.Space,
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
    

