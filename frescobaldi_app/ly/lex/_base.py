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
The State implementation.

Don't use this module directly!
All important classes are imported in the ly.lex namespace.

This module starts with an underscore so that it does not interfere with the mode
modules.

"""

from __future__ import unicode_literals

from _parser import FallthroughParser


class State(object):
    """Maintains state while parsing a text for LilyPond input.
    
    Basically, you create a State object and then use it with the tokens()
    generator to tokenize a text string of LilyPond input.
    
    """
    def __init__(self, initialParserClass):
        self.state = [initialParserClass()]
    
    def tokens(self, text, pos=0):
        """Parses a text string using our state info.
        
        Yields Token instances.  All tokens are a subclass of unicode. Also
        space tokens are returned.  All tokens have a pos and an end attribute,
        describing their position in the original string.
        
        """
        while True:
            parser = self.parser()
            m = parser.parse(text, pos)
            if m:
                if pos < m.start():
                    yield parser.default(text[pos:m.start()], pos, self)
                yield parser.token(m, self)
                pos = m.end()
            elif parser.fallthrough(self):
                break
            continue
        if pos < len(text):
            yield parser.default(text[pos:], pos, self)
    
    def freeze(self):
        """Returns the current state as a tuple (hashable object)."""
        return tuple((
            parser.__class__,
            parser.argcount,
        ) for parser in self.state)
    
    @classmethod
    def thaw(cls, frozen):
        """Returns a new State object from the frozen state argument."""
        obj = object.__new__(cls)
        obj.state = []
        for cls, argcount in frozen:
            parser = cls(argcount)
            obj.state.append(parser)
        return obj
        
    def parser(self, depth=-1):
        """Returns the current Parser."""
        return self.state[depth]
        
    def parsers(self):
        """Iterates over the list of parsers, most current first."""
        return self.state[::-1]
        
    def enter(self, parserClass, argcount=None):
        """Enter a new parser."""
        self.state.append(parserClass(argcount))
        
    def replace(self, parserClass, argcount=None):
        """Enter a new parser, replacing the current one."""
        self.state[-1] = parserClass(argcount)
        
    def leave(self):
        """Leave the current parser and pop back to the previous."""
        if len(self.state) > 1:
            self.state.pop()
    
    def endArgument(self):
        """Decrease argcount and leave the parser if it would reach 0."""
        while len(self.state) > 1:
            if self.state[-1].argcount == 1:
                self.state.pop()
            else:
                if self.state[-1].argcount > 0:
                    self.state[-1].argcount -= 1
                return
    
    def __len__(self):
        """Returns the number of parsers currently in the stack."""
        return len(self.state)

    def followToken(self, token):
        """Act as if the token has been instantiated with the current state.
        
        Changes state according to the token.
        
        """
        if isinstance(self.parser(), FallthroughParser) and token.__class__ not in self.parser().items:
            self.parser().fallthrough(self)
        token.changeState(self)

    def mode(self):
        """Returns the mode attribute of the first parser (from current parser) that has it."""
        for parser in self.parsers():
            try:
                return parser.mode
            except AttributeError:
                pass

