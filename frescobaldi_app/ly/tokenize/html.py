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
    Parser,
    Token,
    Space,
    Leaver,
    StringBase,
    StringParserBase,
    CommentBase,
)


class Comment(CommentBase):
    pass


class CommentStart(Comment):
    rx = r"<!--"
    def __init__(self, matchObj, state):
        state.enter(CommentParser)
        
        
class CommentEnd(Comment, Leaver):
    rx = r"-->"


class String(StringBase):
    pass


class TagStart(Token):
    rx = r"</?\w[-_:\w]*\b"
    def __init__(self, matchObj, state):
        state.enter(AttrParser)
        

class TagEnd(Leaver):
    rx = r"/?>"
    

class AttrName(Token):
    rx = r"\w+([-_:]\w+)?"
    
    
class EqualSign(Token):
    rx = "="


class StringDQStart(String):
    rx = r'"'
    def __init__(self, matchObj, state):
        state.enter(StringDQParser)


class StringSQStart(String):
    rx = r"'"
    def __init__(self, matchObj, state):
        state.enter(StringSQParser)
    

class StringEnd(String, Leaver):
    pass


class StringDQEnd(StringEnd):
    rx = r'"'
    

class StringSQEnd(StringEnd):
    rx = r"'"


class EntityRef(Token):
    rx = r"\&(#\d+|#[xX][0-9A-Fa-f]+|[A-Za-z_:][\w.:_-]*);"

# Parsers:

class HTMLParser(Parser):
    items = (
        Space,
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
    defaultClass = String
    items = (
        StringDQEnd,
        EntityRef,
    )
    

class StringSQParser(StringParserBase):
    defaultClass = String
    items = (
        StringSQEnd,
        EntityRef,
    )
    

class CommentParser(Parser):
    defaultClass = Comment
    items = (
        CommentEnd,
    )


