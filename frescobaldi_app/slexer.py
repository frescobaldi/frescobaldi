# === Python slexer (Stateful Lexer) module ===
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
slexer -- Stateful Lexer

parses text, searching for tokens represented by a regular expression.

Only depends on the standard Python re module.

You need to create at least one subclass of Parser, and a subclass of Token for
every type of text to search for. Then you list the token class names in the
'items' tuple of the Parser subclass definition.

Different contexts can be parsed by creating multiple Parser subclasses.
A Parser searches for tokens using the list of Token classes. (Token is simply a
subclass of str in Python 3 and of unicode in Python 2). Every Token subclass
has the regular expression part to search for in its 'rx' class attribute.

You start parsing text by instantiating a State (you don't need to subclass
that) with the Parser subclass you want to parse the text with. Then you iterate
over the generated tokens using the tokens(text) method of the State instance.
You can use the tokens just as strings (e.g. if token == 'text'...) but you can
also test for the type of the token (e.g. if isinstance(token, Number)...).
The tokens also carry a 'pos' and an 'end' attribute, specifying their position
in the parsed text string.

A token may cause a different Parser to be enterend, of the current Parser to be
left, etc. This is done by implementing the update_state() method of the Token
subclass. This method is called automatically when the Token is instantiated.

The State maintains the parsing state (the list of active Parser instances).
A State can be frozen to be thawn later to resume parsing text starting in a
particular context. A Fridge can be used to store and recover a state under a
simple integer number.

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
    def update_state(self, state):
        state.enter(PString())

class StringEnd(String):
    rx = '"'
    def update_state(self, state):
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
    print(t.__class__, t)

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
    
    The state is basically a list of Parser instances; the last one is the
    active one. The enter() and leave() methods respectively enter a new parser
    or leave the current parser.
    
    You can't leave() the initial parser instance.
    
    """
    def __init__(self, initialParserClass):
        """Construct the State with an initial Parser instance."""
        self.state = [initialParserClass()]
    
    def parser(self):
        """Return the currently active Parser instance."""
        return self.state[-1]
    
    def parsers(self):
        """Return all active parsers, the most current one first."""
        return self.state[::-1]
    
    def tokens(self, text, pos=0):
        """Parse a text string using our state info.
        
        Yields Token instances. All tokens are a subclass of str (or unicode in
        Python 2.x) and have a pos and an end attribute, describing their
        position in the original string. If the current parser defines a
        'default' class attribute, it is the Token subclass to use for pieces of
        text that would otherwise be skipped.
        
        """
        while True:
            parser = self.parser()
            m = parser.parse(text, pos)
            if m:
                if parser.default and pos < m.start():
                    token =  parser.default(text[pos:m.start()], pos)
                    token.update_state(self)
                    yield token
                token = parser.token(m)
                token.update_state(self)
                yield token
                pos = m.end()
            elif pos == len(text) or parser.fallthrough(self):
                break
        if parser.default and pos < len(text):
            token = parser.default(text[pos:], pos)
            token.update_state(self)
            yield token
    
    def enter(self, parser):
        """Enter a new parser.
        
        Note: 'parser' is an instantiated Parser subclass.
        Most times this method will be called from with the update_state()
        method of a Token subclass (or from a Parser subclass, which is also
        possible: the default implementation of Token.update_state() calls
        Parser.update_state(), which does nothing by default).
        
        E.g. in the Token subclass:
        
            def update_state(self, state):
                state.enter(SomeDifferentParser())
        
        """
        self.state.append(parser)
        
    def leave(self):
        """Leave the current parser and pop back to the previous.
        
        The first parser (specified on instantiation) will never be left.
        
        """
        if len(self.state) > 1:
            self.state.pop()
    
    def replace(self, parser):
        """Replace the current parser with a new one.
        
        Somewhat equivalent to:
            state.leave()
            state.enter(SomeDifferentParser)
        
        But using this method you can also replace the first parser.
        
        """
        self.state[-1] = parser
    
    def depth(self):
        """Return the number of parsers currenly active (1 or more).
        
        You can use this e.g. to keep parsing until some context ends:
        
        tokens = state.tokens(text) # iterator
        depth = state.depth()
        for token in tokens:
            if state.depth() < depth:
                break
            # do something
        
        """
        return len(self.state)
    
    def follow(self, token):
        """Act as if the token has been instantiated with the current state.
        
        You need this when you already have the parsed tokens, (e.g. cached or
        saved somehow) but want to know which parser created them.
        
        This method changes state according to the token. Basically it calls the
        update_state() method of the token instance, but it does some more work
        behind the scenes to ensure that the FallthroughParser type (see below)
        also is handled correctly.
        
        """
        while self.parser()._follow(token, self):
            pass
        token.update_state(self)

    def freeze(self):
        """Return the current state as a tuple (hashable object)."""
        return tuple((p.__class__, p.freeze()) for p in self.state)
    
    @classmethod
    def thaw(cls, frozen):
        """Reproduce a State object from the frozen state argument."""
        state = cls.__new__(cls)
        state.state = [cls.thaw(attrs) for cls, attrs in frozen]
        return state
        

class Token(str):
    """Represents a parsed piece of text.
    
    The subclass determines the type.
    
    You should put the regular expression string in the rx class attribute.
    In the rx string, you may not use named groups starting with "g_".
    
    To add token types to a Parser class, list the token class in the items
    attribute of the Parser class.
    
    """
    __slots__ = ['pos', 'end']
    
    rx = None
    
    @classmethod
    def test_match(cls, match):
        """Should return True if the match should indeed instantiate this class.
        
        This class method is only called if multiple Token classes in the
        Parser's items list have the same rx attribute. This method is then
        called for every matching Token subclass until one returns True.
        That token is then instantiated. (The method is not called for the last
        class in the list that have the same rx attribute, and also not if there
        is only one class with that rx attribute.)
        
        The default implementation always returns True.
        
        """
        return True
    
    def __new__(cls, string, pos):
        token = str.__new__(cls, string)
        token.pos = pos
        token.end = pos + len(token)
        return token
        
    def update_state(self, state):
        """Lets the token update the state, e.g. enter a different parser.
        
        This method is called by the State upon instantiation of the tokens.
        
        Don't use it later on to have a State follow already instantiated Tokens
        because the FallthroughParser type can also change the state without
        generating a Token. Use State.follow() to have a State follow
        instantiated Tokens.
        
        The default implementation lets the Parser decide on state change.
        
        """
        state.parser().update_state(state, self)


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
            # if Token classes have the same regexp string, group them
            patterns = []
            counter = {}
            for cls in uniq(owner.items):
                rx = cls.rx
                try:
                    counter[rx].append(cls)
                except KeyError:
                    counter[rx] = [cls]
                    patterns.append(rx)
            # make the pattern
            owner.pattern = self.pattern = pattern = re.compile("|".join(
                "(?P<g_{0}>{1})".format(i, rx)
                for i, rx in enumerate(patterns)), owner.re_flags)
            # make a fast mapping list from matchObj.lastindex to the token class
            indices = sorted(v for k, v in pattern.groupindex.items() if k.startswith('g_'))
            owner.index = self.index = index = [None] * (indices[-1] + 1)
            for i, rx in zip(indices, patterns):
                index[i] = counter[rx]
        return owner.pattern


class ParserMeta(type):
    """Metaclass for Parser subclasses.
    
    Adds a 'pattern' attribute with a PatternProperty() when the class also
    defines 'items'.
    
    """
    def __new__(cls, name, bases, attrd):
        if attrd.get('items'):
            attrd['pattern'] = PatternProperty()
        return type.__new__(cls, name, bases, attrd)


class Parser(object):
    """Abstract base class for Parsers.
    
    When creating Parser subclasses, you should set the 'items' attribute to a
    tuple of Token subclasses. On class construction, a large regular expression
    pattern is built by combining the expressions from the 'rx' attributes of
    the Token subclasses.
    
    Additionally, you may implement the update_state() method which is called
    by the default implementation of update_state() in Token.
    
    """
    re_flags = 0   # the re.compile flags to use
    default = None # if not None, the default class for unparsed pieces of text
    
    # tuple of Token classes to look for in text
    items = ()
    
    def parse(self, text, pos):
        """Parse text from position pos and returns a Match Object or None."""
        return self.pattern.search(text, pos)
    
    def token(self, match):
        """Return a Token instance of the correct class.
        
        The match object is returned by the parse() method.
        
        """
        clss = self.index[match.lastindex]
        for c in clss[:-1]:
            if c.test_match(match):
                return c(match.group(), match.start())
        return clss[-1](match.group(), match.start())
    
    def _follow(self, token, state):
        """(Internal) Called by State.follow(). Does nothing."""
        pass
    
    def freeze(self):
        """Return our instance values as a hashable tuple."""
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

    def update_state(self, state, token):
        """Called by the default implementation of Token.update_state().
        
        Does nothing by default.
        
        """
        pass


# This syntax to make Parser use the metaclass works in both Python2 and 3
Parser = ParserMeta(Parser.__name__, Parser.__bases__, dict(Parser.__dict__))


class FallthroughParser(Parser):
    """Base class for parsers that 'match' instead of 'search' for a pattern.
    
    You can also implement the fallthrough() method to do something with
    the state if there is no match. The default is to leave the current parser.
    See Parser().
    
    """
    def parse(self, text, pos):
        """Match text at position pos and returns a Match Object or None."""
        return self.pattern.match(text, pos)
    
    def _follow(self, token, state):
        """(Internal) Called by State.follow().
        
        Falls through if the token can't have been generated by this parser.
        
        """
        if type(token) not in self.items:
            self.fallthrough(state)
            return True

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
        if 0 <= num < len(self._states):
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
        def update_state(self, state):
            state.enter(PString())
    
    class StringEnd(String):
        rx = '"'
        def update_state(self, state):
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


