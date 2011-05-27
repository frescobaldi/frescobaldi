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
Base classes for Parser instances.

You can import this module in you mode modules to subclasse Parser or FallthroughParser.

This module starts with an underscore so that it does not interfere with the mode
modules.

"""

from __future__ import unicode_literals

__all__ = ["Parser", "FallthroughParser"]


import re

import _token


# list of all token classes, the index is used as groupname for the parser's regexp
_tokenclasses = []


class PatternProperty(object):
    """A descriptor that lazily generates a regular expression based on a list of Token subclasses."""
    def __init__(self, items):
        self.items = items
    
    def __get__(self, instance, owner):
        try:
            return self.pattern
        except AttributeError:
            self.pattern = re.compile("|".join(self.generate()))
        return self.pattern

    def generate(self):
        done = set()
        for cls in self.items:
            if cls not in done:
                done.add(cls) # avoid having the same class twice in the same regexp
                try:
                    index = _tokenclasses.index(cls)
                except ValueError:
                    index = len(_tokenclasses)
                    _tokenclasses.append(cls)
                yield "(?P<g{0}>{1})".format(index, cls.rx)
        

class ParserMetaClass(type):
    """Metaclass for Parser subclasses.
    
    Reads the items class attribute and create a (lazily created) compiled regex pattern
    to parse text for those items.
    
    """
    def __new__(cls, name, bases, attrd):
        try:
            attrd['pattern'] = PatternProperty(attrd['items'])
        except KeyError:
            pass # in abstract classes there is no items attribute
        return type.__new__(cls, name, bases, attrd)


class Parser(object):
    """Abstract base class for parsers.  Must be subclassed."""
    
    __metaclass__ = ParserMetaClass
    
    argcount = 0
    default = _token.Unparsed
    
    def __init__(self, argcount = None):
        if argcount is not None:
            self.argcount = argcount
    
    def parse(self, text, pos):
        return self.pattern.search(text, pos)

    def token(self, matchObj, state):
        """Returns a Token instance of the correct class, based on the given matchObj.
        
        The matchObj is returned by the parse() method and its lastgroup attribute
        points to the correct Token subclass in the global _tokenclasses class list.
        
        """
        tokenClass = _tokenclasses[int(matchObj.lastgroup[1:])]
        return tokenClass(matchObj.group(), matchObj.start(), state)
        
    def fallthrough(self, state):
        """Called when no match is returned by parse().
        
        If this function returns True, the tokenizer stops parsing, assuming all
        text has been consumed.  If this function returns False or None, it
        should alter the state (switch parsers) and parsing continues using the
        new Parser.
        
        The default implementation simply returns True.
        
        """
        return True

    def changeState(self, state, token):
        """Called by the default implementation of Token.changeState()."""
        pass


class FallthroughParser(Parser):
    """Base class for parsers that 'match' instead of 'search' for a pattern.
    
    You should also implement the fallthrough() method to do something with
    the state if there is no match. The default is to leave the current parser.
    See Parser().
    
    """
    def parse(self, text, pos):
        return self.pattern.match(text, pos)
    
    def fallthrough(self, state):
        state.leave()


