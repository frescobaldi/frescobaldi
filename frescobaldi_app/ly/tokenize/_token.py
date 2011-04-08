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
Token base classes.

Don't use this module directly!
All important classes are imported in the ly.tokenize namespace.

You can, however, import _token in mode modules that also are in this directory.

This module starts with an underscore so that it does not interfere with the mode
modules.

"""

from __future__ import unicode_literals

class Token(unicode):
    """Represents a parsed piece of text.
    
    The subclass determines the type.
    
    The state can be manipulated on instantiation, and also
    by calling the changeState() method, e.g. when iterating over
    the tokens again.
    
    """
    __slots__ = ['pos', 'end']
    
    def __new__(cls, string, pos, state):
        token = unicode.__new__(cls, string)
        token.pos = pos
        token.end = pos + len(token)
        token.changeState(state)
        return token
        
    def changeState(self, state):
        """Implement this to have this token change the state, e.g. enter a different parser.
        
        Don't use it later on to have a State follow already instantiated Tokens,
        because the FallthroughParser type can also change the state without generating a Token.
        Use State.followToken() to have a State follow instantiated Tokens.
        
        The default implementation lets the Parser decide on state change.
        
        """
        state.parser().changeState(state, self)


class Unparsed(Token):
    """Represents an unparsed piece of input text."""


# some token types with special behaviour:
class Item(Token):
    """A token that decreases the argument count of the current parser."""
    def changeState(self, state):
        state.endArgument()


class Leaver(Token):
    """A token that leaves the current parser."""
    def changeState(self, state):
        state.leave()


# some generic types:
class Space(Token):
    """A token containing whitespace."""
    rx = r'\s+'


class Newline(Token):
    """A token that is a single newline."""
    rx = r'\n'


# some base types that should be inherited:
class Comment(Token):
    """Base class for tokens that belong to a comment."""


class LineComment(Comment):
    """Base class for items that are a whole line comment."""
    
    
class BlockComment(Comment):
    """Base class for tokens that belong to a block/multiline comment."""


class BlockCommentStart(BlockComment):
    """Base class for tokens that start a block/multiline comment."""


class BlockCommentEnd(BlockComment):
    """Base class for tokens that end a block/multiline comment."""


class String(Token):
    """Base class for tokens that belong to a quote-delimited string."""
    
    
class StringStart(String):
    """Base class for tokens that start a quote-delimited string."""
    
    
class StringEnd(String):
    """Base class for tokens that end a quote-delimited string."""
    
    
class Character(Token):
    """Base class for tokens that are an (escaped) character."""
    
    
class Numeric(Token):
    """Base class for tokens that are a numerical value."""
    
    
class Error(Token):
    """Base class for tokens that represent erroneous input."""


# some mixin classes that make special handling of tokens possible besides correct parsing:

# MatchEnd and MatchStart can be used by parenthesis/brace matcher.
# the matchname class attribute defines the type, so that it is independent
# of the way other types could be nested.
class MatchStart(object):
    """Mixin class for tokens that have a matching token forward in the text.
    
    The matchname attribute should give a unique name.
    
    """
    matchname = ""


class MatchEnd(object):
    """Mixin class for tokens that have a matching token backward in the text.
    
    The matchname attribute should give a unique name.
    
    """
    matchname = ""


# Indent and Dedent can be used by an (auto) indenter.
class Indent(object):
    """Mixin class for tokens that have the text on the next line indent more."""


class Dedent(object):
    """Mixin class for tokens that have the text on the next line indent less."""


