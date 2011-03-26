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

from __future__ import unicode_literals

"""
Parses and tokenizes HTML input, recognizing LilyPond in HTML.
"""

import _token
import _parser

import lilypond


class Comment(_token.Comment):
    pass


class CommentStart(Comment, _token.BlockCommentStart):
    rx = r"<!--"
    def changeState(self, state):
        state.enter(CommentParser)
        
        
class CommentEnd(Comment, _token.Leaver, _token.BlockCommentEnd):
    rx = r"-->"


class String(_token.String):
    pass


class Tag(_token.Token):
    pass


class TagStart(Tag):
    rx = r"</?\w[-_:\w]*\b"
    def changeState(self, state):
        state.enter(AttrParser)
        

class TagEnd(Tag, _token.Leaver):
    rx = r"/?>"
    

class AttrName(_token.Token):
    rx = r"\w+([-_:]\w+)?"
    
    
class EqualSign(_token.Token):
    rx = "="
    def changeState(self, state):
        state.enter(ValueParser)


class Value(_token.Leaver):
    rx = r"\w+"
    

class StringDQStart(String, _token.StringStart):
    rx = r'"'
    def changeState(self, state):
        state.enter(StringDQParser)


class StringSQStart(String, _token.StringStart):
    rx = r"'"
    def changeState(self, state):
        state.enter(StringSQParser)
    

class StringDQEnd(String, _token.StringEnd, _token.Leaver):
    rx = r'"'
    

class StringSQEnd(String, _token.StringEnd, _token.Leaver):
    rx = r"'"


class EntityRef(_token.Character):
    rx = r"\&(#\d+|#[xX][0-9A-Fa-f]+|[A-Za-z_:][\w.:_-]*);"


class LilyPondTag(Tag):
    pass


class LilyPondVersionTag(LilyPondTag):
    rx = r"<lilypondversion/?>"


class LilyPondFileTag(LilyPondTag):
    rx = r"</?lilypondfile\b"
    def changeState(self, state):
        state.enter(LilyPondFileOptionsParser)


class LilyPondFileTagEnd(LilyPondTag, _token.Leaver):
    rx = r"/?>"


class LilyPondInlineTag(LilyPondTag):
    rx = r"<lilypond\b"
    def changeState(self, state):
        state.enter(LilyPondAttrParser)


class LilyPondCloseTag(LilyPondTag, _token.Leaver):
    rx = r"</lilypond>"
    
    
class LilyPondTagEnd(LilyPondTag):
    rx = r">"
    def changeState(self, state):
        state.replace(LilyPondParser)


class LilyPondInlineTagEnd(LilyPondTag, _token.Leaver):
    rx = r"/?>"
    

class SemiColon(_token.Token):
    rx = r":"
    def changeState(self, state):
        state.replace(LilyPondInlineParser)



# Parsers:

class HTMLParser(_parser.Parser):
    items = (
        _token.Space,
        LilyPondVersionTag,
        LilyPondFileTag,
        LilyPondInlineTag,
        CommentStart,
        TagStart,
        EntityRef,
    )


class AttrParser(_parser.Parser):
    items = (
        _token.Space,
        TagEnd,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
    )


class StringDQParser(_parser.Parser):
    default = String
    items = (
        StringDQEnd,
        EntityRef,
    )
    

class StringSQParser(_parser.Parser):
    default = String
    items = (
        StringSQEnd,
        EntityRef,
    )
    

class CommentParser(_parser.Parser):
    default = Comment
    items = (
        CommentEnd,
    )


class ValueParser(_parser.FallthroughParser):
    """Finds a value or drops back."""
    items = (
        _token.Space,
        Value,
    )
    def fallthrough(self, state):
        state.leave()


class LilyPondAttrParser(_parser.Parser):
    items = (
        _token.Space,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
        LilyPondTagEnd,
        SemiColon,
    )
    

class LilyPondFileOptionsParser(_parser.Parser):
    items = (
        _token.Space,
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
    

