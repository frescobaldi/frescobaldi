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
Parses and tokenizes HTML input, recognizing LilyPond in HTML.
"""

from __future__ import unicode_literals

from . import _token
from . import Parser, FallthroughParser

from . import lilypond


class Comment(_token.Comment):
    pass


class CommentStart(Comment, _token.BlockCommentStart):
    rx = r"<!--"
    def update_state(self, state):
        state.enter(ParseComment())
        
        
class CommentEnd(Comment, _token.Leaver, _token.BlockCommentEnd):
    rx = r"-->"


class String(_token.String):
    pass


class Tag(_token.Token):
    pass


class TagStart(Tag):
    rx = r"</?\w[-_:\w]*\b"
    def update_state(self, state):
        state.enter(ParseAttr())
        

class TagEnd(Tag, _token.Leaver):
    rx = r"/?>"
    

class AttrName(_token.Token):
    rx = r"\w+([-_:]\w+)?"
    
    
class EqualSign(_token.Token):
    rx = "="
    def update_state(self, state):
        state.enter(ParseValue())


class Value(_token.Leaver):
    rx = r"\w+"
    

class StringDQStart(String, _token.StringStart):
    rx = r'"'
    def update_state(self, state):
        state.enter(ParseStringDQ())


class StringSQStart(String, _token.StringStart):
    rx = r"'"
    def update_state(self, state):
        state.enter(ParseStringSQ())
    

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
    def update_state(self, state):
        state.enter(ParseLilyPondFileOptions())


class LilyPondFileTagEnd(LilyPondTag, _token.Leaver):
    rx = r"/?>"


class LilyPondInlineTag(LilyPondTag):
    rx = r"<lilypond\b"
    def update_state(self, state):
        state.enter(ParseLilyPondAttr())


class LilyPondCloseTag(LilyPondTag, _token.Leaver):
    rx = r"</lilypond>"
    
    
class LilyPondTagEnd(LilyPondTag):
    rx = r">"
    def update_state(self, state):
        state.replace(ParseLilyPond())


class LilyPondInlineTagEnd(LilyPondTag, _token.Leaver):
    rx = r"/?>"
    

class SemiColon(_token.Token):
    rx = r":"
    def update_state(self, state):
        state.replace(ParseLilyPondInline())



# Parsers:

class ParseHTML(Parser):
    mode = "html"
    items = (
        _token.Space,
        LilyPondVersionTag,
        LilyPondFileTag,
        LilyPondInlineTag,
        CommentStart,
        TagStart,
        EntityRef,
    )


class ParseAttr(Parser):
    items = (
        _token.Space,
        TagEnd,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
    )


class ParseStringDQ(Parser):
    default = String
    items = (
        StringDQEnd,
        EntityRef,
    )
    

class ParseStringSQ(Parser):
    default = String
    items = (
        StringSQEnd,
        EntityRef,
    )
    

class ParseComment(Parser):
    default = Comment
    items = (
        CommentEnd,
    )


class ParseValue(FallthroughParser):
    """Finds a value or drops back."""
    items = (
        _token.Space,
        Value,
    )
    def fallthrough(self, state):
        state.leave()


class ParseLilyPondAttr(Parser):
    items = (
        _token.Space,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
        LilyPondTagEnd,
        SemiColon,
    )
    

class ParseLilyPondFileOptions(Parser):
    items = (
        _token.Space,
        AttrName,
        EqualSign,
        StringDQStart,
        StringSQStart,
        LilyPondFileTagEnd,
    )


class ParseLilyPond(lilypond.ParseGlobal):
    items = (
        LilyPondCloseTag,
    ) + lilypond.ParseGlobal.items
    

class ParseLilyPondInline(lilypond.ParseMusic):
    items = (
        LilyPondInlineTagEnd,
    ) + lilypond.ParseMusic.items
    

