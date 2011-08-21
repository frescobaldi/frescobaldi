# === Python slexer (Stateful Lexer) module ===
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
slexer -- Stateful Lexer

parses text, searching for tokens represented by a regular expression.

Only depends on the standard Python re module.

Different contexts can be parsed by creating Parser subclasses.
A Parser searches for tokens using a list of Token classes. (Token is a subclass
of str in Python 3 and of unicode in Python 2). Every Token class has a class
attribute containing the regular expression to search for.

The parser yields Token instances. A token may cause a different Parser to be
enterend, of the current Parser to be left, etc. This is done by implementing
the updateState() method of the Token subclass.

The State maintains the parsing state (the list of active Parser instances).

A State can be frozen to be thawn later to resume parsing text starting
in a particular context. A Fridge can be used to store and recover a state under
a simple integer number.

How to use slexer:

from slexer import Token, Parser, State

# create token classes:
class Word(Token):
    rx = r'\w+'

class Number(Token):
    rx = r'\d+'

class String(Token):
    pass

class StringStart(String):
    rx = '"'
    def updateState(self, state):
        state.enter(PString())

class StringEnd(String):
    rx = '"'
    def updateState(self, state):
        state.leave()

# create parsers:
class PTest(Parser):
    '''Looks for numbers, words and the double quote.'''
    items = (
        Number,
        Word,
        StringStart,
    )

class PString(Parser):
    '''Returns String by default, quits at double quote.'''
    default = String
    items = (
        StringEnd,
    )

s = State(PTest)
for t in s.tokens(
    'een tekst met 7 woorden, '
    'een "tekst met 2 aanhalingstekens" '
    'en 2 of 3 nummers'):
    print t.__class__, t

# results in:
<class '__main__.Word'> een
<class '__main__.Word'> tekst
<class '__main__.Word'> met
<class '__main__.Number'> 7
<class '__main__.Word'> woorden
<class '__main__.Word'> een
<class '__main__.StringStart'> "
<class '__main__.String'> tekst met 2 aanhalingstekens
<class '__main__.StringEnd'> "
<class '__main__.Word'> en
<class '__main__.Number'> 2
<class '__main__.Word'> of
<class '__main__.Number'> 3
<class '__main__.Word'> nummers

"""

# remove the following 5 lines if sure Python 3.x is used
from __future__ import unicode_literals
import sys
if sys.version_info[0] < 3:
    str = unicode
del sys


import re


__all__ = ['Token', 'Parser', 'FallthroughParser', 'State', 'Fridge']


class State(object):
    """Maintains state while parsing text.
    
    You instantiate a State object with an initial parser class.
    Then you use tokens(text) to start parsing for tokens.
    
    The state is simply a list of Parser instances; the last one is the active
    one. The enter() and leave() methods respectively enter a new parser or
    leave the current parser (although the initial parser can never be left).
    
    """
    def __init__(self, initialParserClass):
        """Construct the State with an initial Parser instance."""
        self.state = [initialParserClass()]
    
    def parser(self):
        """Returns the current Parser instance."""
        return self.state[-1]
        
    def tokens(self, text, pos=0):
        """Parses a text string using our state info.
        
        Yields Token instances. All tokens are a subclass of str (or unicode in
        Python 2.x) and have a pos and an end attribute, describing their
        position in the original string. If the current parser defines a
        'default' class attribute, it is the Token subclass to use for otherwise
        unparsed pieces of text.
        
        """
        while True:
            parser = self.parser()
            m = parser.parse(text, pos)
            if m:
                if parser.default and pos < m.start():
                    yield parser.default(text[pos:m.start()], pos, self)
                yield parser.token(m, self)
                pos = m.end()
            elif parser.fallthrough(self):
                break
        if parser.default and pos < len(text):
            yield parser.default(text[pos:], pos, self)
    
    def enter(self, parser):
        """Enter a new parser."""
        self.state.append(parser)
        
    def leave(self):
        """Leave the current parser and pop back to the previous."""
        if len(self.state) > 1:
            self.state.pop()
    
    def follow(self, token):
        """Act as if the token has been instantiated with the current state.
        
        Changes state according to the token.
        
        """
        self.parser()._follow(token, self)
        token.updateState(self)

    def freeze(self):
        """Returns the current state as a tuple (hashable object)."""
        return tuple((p.__class__, p.freeze()) for p in self.state)
    
    @classmethod
    def thaw(cls, frozen):
        """Reproduces a State object from the frozen state argument."""
        state = cls.__new__(cls)
        state.state = [cls.thaw(attrs) for cls, attrs in frozen]
        return state
        

class Token(str):
    """Represents a parsed piece of text.
    
    The subclass determines the type.
    
    You should put the regular expression string in the rx class attribute.
    In the rx string, you may not use named groups starting with "g_".
    Upon instantiation, the updateState() instance method is also called.
    
    To add token types to a Parser class, list the token class in the items
    attribute of the Parser class.
    
    """
    __slots__ = ['pos', 'end']
    
    rx = None
    
    def __new__(cls, string, pos, state):
        token = str.__new__(cls, string)
        token.pos = pos
        token.end = pos + len(token)
        token.updateState(state)
        return token
        
    def updateState(self, state):
        """Lets the token update the state, e.g. enter a different parser.
        
        Don't use it later on to have a State follow already instantiated Tokens
        because the FallthroughParser type can also change the state without
        generating a Token. Use State.follow() to have a State follow
        instantiated Tokens.
        
        The default implementation lets the Parser decide on state change.
        
        """
        state.parser().updateState(state, self)


class PatternProperty(object):
    """A descriptor that lazily generates a regular expression.
    
    The expression is based on the list of Token subclasses in the items
    attribute of a Parser class. Also creates an index attribute for the parser
    class that maps the lastindex property of a match object to the token class.
    
    When the pattern is requested for the first time, it is created and also
    written in the class, overwriting this descriptor.
    
    """
    def __get__(self, instance, owner):
        try:
            owner.pattern = self.pattern
            owner.index = self.index
        except AttributeError:
            clss = list(uniq(owner.items))
            # make the pattern
            owner.pattern = self.pattern = pattern = re.compile("|".join(
                "(?P<g_{0}>{1})".format(i, cls.rx) for i, cls in enumerate(clss)))
            # make a fast mapping list from matchObj.lastindex to the token class
            indices = sorted(v for k, v in pattern.groupindex.items() if k.startswith('g_'))
            owner.index = self.index = index = [None] * (indices[-1] + 1)
            for i, cls in zip(indices, clss):
                index[i] = cls
        return owner.pattern


class ParserMeta(type):
    """Metaclass for Parser subclasses.
    
    Adds a 'pattern' attribute with a PatternProperty() when the class also
    defines 'items'.
    
    """
    def __new__(cls, name, bases, attrd):
        if 'items' in attrd:
            attrd['pattern'] = PatternProperty()
        return type.__new__(cls, name, bases, attrd)


class Parser(object):
    """Abstract base class for Parsers.
    
    When creating Parser subclasses, you should set the 'items' attribute to a
    tuple of Token subclasses.
    
    Additionally, you may implement the updateState() method which is called
    by the default implementation of updateState() in Token.
    
    """
    __metaclass__ = ParserMeta
    
    default = None # if not None, the default class for unparsed pieces of text
    
    # tuple of Token classes to look for in text
    items = ()
    
    def parse(self, text, pos):
        """Parses text from position pos and returns a Match Object or None."""
        return self.pattern.search(text, pos)
    
    def token(self, matchObj, state):
        """Returns a Token instance of the correct class.
        
        The matchObj is returned by the parse() method.
        
        """
        tokenClass = self.index[matchObj.lastindex]
        return tokenClass(matchObj.group(), matchObj.start(), state)
        
    def _follow(self, token, state):
        """(Internal) Called by State.follow()."""
        pass
    
    def freeze(self):
        """Should return our instance values as a hashable tuple."""
        return ()
    
    @classmethod
    def thaw(cls, attrs):
        return cls(*attrs)

    def fallthrough(self, state):
        """Called when no match is returned by parse().
        
        If this function returns True, the tokenizer stops parsing, assuming all
        text has been consumed.  If this function returns False or None, it
        should alter the state (switch parsers) and parsing continues using the
        new Parser.
        
        The default implementation simply returns True.
        
        """
        return True

    def updateState(self, state, token):
        """Called by the default implementation of Token.updateState().
        
        Does nothing by default.
        
        """
        pass


class FallthroughParser(Parser):
    """Base class for parsers that 'match' instead of 'search' for a pattern.
    
    You can also implement the fallthrough() method to do something with
    the state if there is no match. The default is to leave the current parser.
    See Parser().
    
    """
    def parse(self, text, pos):
        """Matches text at position pos and returns a Match Object or None."""
        return self.pattern.match(text, pos)
    
    def _follow(self, token, state):
        """(Internal) Called by State.follow()."""
        if not isinstance(token, self.items):
            self.fallthrough(state)

    def fallthrough(self, state):
        """Called when no match is returned by parse().
        
        This implementation leaves the current parser and returns None
        (causing the State to continue parsing).
        
        """
        state.leave()


class Fridge(object):
    """Stores frozen States under an integer number."""
    def __init__(self, stateClass = State):
        self._stateClass = stateClass
        self._states = []
    
    def freeze(self, state):
        """Stores a state and return an identifying integer."""
        frozen = state.freeze()
        try:
            return self._states.index(frozen)
        except ValueError:
            i = len(self._states)
            self._states.append(frozen)
            return i

    def thaw(self, num):
        """Returns the state stored under the specified number."""
        return self._stateClass.thaw(self._states[num])

    def count(self):
        """Returns the number of stored frozen states."""
        return len(self._states)


def uniq(iterable):
    """Yields unique items from iterable."""
    seen, l = set(), 0
    for i in iterable:
        seen.add(i)
        if len(seen) > l:
            yield i
            l = len(seen)


if __name__ == "__main__":
    # test
    class Word(Token):
        rx = r'\w+'
    
    class Number(Token):
        rx = r'\d+'
    
    class String(Token):
        pass
    
    class StringStart(String):
        rx = '"'
        def updateState(self, state):
            state.enter(PString())
    
    class StringEnd(String):
        rx = '"'
        def updateState(self, state):
            state.leave()
    
    class PTest(Parser):
        items = (
            Number,
            Word,
            StringStart,
        )
    
    class PString(Parser):
        default = String
        items = (
            StringEnd,
        )
    
    s = State(PTest)
    print('test:')
    for t in s.tokens(
        'een tekst met 7 woorden, '
        'een "tekst met 2 aanhalingstekens" '
        'en 2 of 3 nummers'):
        print(t.__class__, t)

    print('test the Fridge:')
    s = State(PTest)
    f = Fridge()
    
    for t in s.tokens('text with "part of a '):
        print(t.__class__, t)
    
    n = f.freeze(s)
    
    # recover
    print('freeze and recover:')
    s = f.thaw(n)
    for t in s.tokens('quoted string" in the middle'):
        print(t.__class__, t)


