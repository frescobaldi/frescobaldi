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
Token base classes.

Don't use this module directly!
All important classes are imported in the ly.lex namespace.

You can, however, import _token in mode modules that also are in this directory.

This module starts with an underscore so that its name does not interfere with
the mode modules.

"""

from __future__ import unicode_literals


import slexer


class Token(slexer.Token):
    def __repr__(self):
        c = self.__class__
        module = c.__module__.rsplit('.', 1)[-1]
        name = c.__name__
        contents = slexer.Token.__repr__(self)
        where = self.pos
        return '<{0}.{1} {2} at {3}>'.format(module, name, contents, where)


class patternproperty(object):
    """Property that caches the return value of its function and returns that next time.
    
    Use this if the rx attribute (the pattern string to match tokens for) of a Token subclass
    is already costly to create and you want it created lazily (i.e. only when parsing starts):
    
    @patternproperty
    def rx():
        ...complicated function returning the regular expression string...
    
    """
    def __init__(self, func):
        self.func = func
        
    def __get__(self, instance, owner):
        try:
            return self.rx
        except AttributeError:
            self.rx = self.func()
            return self.rx


class Unparsed(Token):
    """Represents an unparsed piece of input text."""


# some token types with special behaviour:
class Item(Token):
    """A token that decreases the argument count of the current parser."""
    def update_state(self, state):
        state.endArgument()


class Leaver(Token):
    """A token that leaves the current parser."""
    def update_state(self, state):
        state.leave()


# some generic types:
class Space(Token):
    """A token containing whitespace."""
    rx = r'\s+'


class Newline(Space):
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


