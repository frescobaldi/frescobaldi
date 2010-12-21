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
Parses and tokenizes LilyPond input.

Also supports LilyPond embedded in HTML, LaTeX, DocBook and Scheme embedded in
LilyPond (and vice versa).
"""


import re

from .. import guessType

_classlist = []


def tokens(text, state=None, pos=0):
    """Parses a text string using state.
    
    If state is not given, starts an anonymous state that guesses the type
    of input (LilyPond, HTML, etc.).
    
    Yields tokens.  All tokens are a subclass of unicode.  Also space tokens
    are returned.  All tokens have a pos and an end attribute, describing their
    position in the original string.
    
    """
    if state is None:
        state = State(guessState(text))
    
    while True:
        parser = state.parser()
        m = parser.parse(text, pos)
        if m:
            if pos < m.start():
                yield parser.default(text[pos:m.start()], pos, state)
            yield _classlist[int(m.lastgroup[1:])](m.group(), m.start(), state)
            pos = m.end()
        elif parser.fallthrough(state):
            break
        continue
    if pos < len(text):
        yield parser.default(text[pos:], pos, state)


def _makePattern(classes):
    """Builds a regular expression to parse a text for the given token classes.
    
    Expects a list of classes representing LilyPond input atoms. Returns a
    compiled regular expression with named groups, to match input of the listed
    types. Reads the rx class attribute of the given classes.
    
    """
    def patterns():
        done = set()
        for cls in classes:
            if cls not in done:
                done.add(cls) # avoid having the same class twice in the same regexp
                try:
                    index = _classlist.index(cls)
                except ValueError:
                    index = len(_classlist)
                    _classlist.append(cls)
                yield "(?P<g{0}>{1})".format(index, cls.rx)
    return re.compile("|".join(patterns()))


class State(object):
    """Maintains state while parsing a text for LilyPond input.
    
    Basically, you create a State object and then use it with the tokens()
    generator to tokenize a text string of LilyPond input.
    
    """
    def __init__(self, initialParserClass=None):
        if initialParserClass is None:
            initialParserClass = lilypond.LilyPondParser
        self.state = [initialParserClass()]
        self.language = 'nederlands' # LilyPond pitch name language
    
    def freeze(self):
        """Returns the current state as a tuple (hashable object)."""
        return tuple((
            parser.__class__,
            parser.level,
            parser.argcount,
        ) for parser in self.state), self.language
    
    @classmethod
    def thaw(cls, frozen):
        """Returns a new State object from the frozen state argument."""
        obj = object.__new__(cls)
        state, obj.language = frozen
        obj.state = []
        for cls, level, argcount in state:
            parser = cls(argcount)
            parser.level = level
            obj.state.append(parser)
        return obj
        
    def parser(self, depth=-1):
        """Returns the current Parser."""
        return self.state[depth]
        
    def enter(self, parserClass, argcount=None):
        """Enter a new parser."""
        self.state.append(parserClass(argcount))
        
    def replace(self, parserClass, argcount=None):
        """Enter a new parser, replacing the current one."""
        self.state.pop()
        self.state.append(parserClass(argcount))
        
    def leave(self):
        """Leave the current parser and pop back to the previous."""
        if len(self.state) > 1:
            self.state.pop()
    
    def endArgument(self):
        """End an argument.
        
        Decrease argcount and leave the parser if it would reach 0.
        
        """
        while len(self.state) > 1 and self.state[-1].level == 0:
            if self.state[-1].argcount > 1:
                self.state[-1].argcount -= 1
                return
            elif self.state[-1].argcount == 0:
                return
            self.state.pop()
            
    def inc(self):
        """Up the level of the current parser.
        
        Indicates nesting while staying in the same parser.
        
        """
        self.state[-1].level += 1
        
    def dec(self):
        """Down the level of the current parser.
        
        If it has reached zero, leave the current parser.
        Otherwise decrease argcount and leave if that would reach zero.
        """
        while self.state[-1].level == 0 and len(self.state) > 1:
            self.state.pop()
        if self.state[-1].level > 0:
            self.state[-1].level -= 1
            self.endArgument()
            
    def depth(self):
        """Return a two-tuple representing the depth of the current state.
        
        This is useful to quickly check when a part of LilyPond input ends.
        
        """
        return len(self.state), self.state[-1].level

    def followToken(self, token):
        """Act as if the token has been instantiated with the current state.
        
        Changes state according to the token.
        
        """
        if isinstance(self.parser(), FallthroughParser) and token.__class__ not in self.parser().items:
            self.parser().fallthrough(self)
        token.changeState(self)


class _makePatternMeta(type):
    """Metaclass for Parser subclasses.
    
    Reads the items class attribute and create a compiled regex pattern
    to parse text for those items.
    
    """
    def __new__(cls, name, bases, attrd):
        try:
            attrd['pattern'] = _makePattern(attrd['items'])
        except KeyError:
            pass # in abstract classes there is no items attribute
        return type.__new__(cls, name, bases, attrd)


class Token(unicode):
    """Represents a parsed piece of LilyPond text.
    
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
        
        """
        pass


class Unparsed(Token):
    """Represents an unparsed piece of input text."""
    pass


# some token types with special behaviour:
class Item(Token):
    """A token that decreases the argument count of the current parser."""
    def changeState(self, state):
        state.endArgument()

class Increaser(Token):
    """A token that increases the level of the current parser."""
    def changeState(self, state):
        state.inc()
        
class Decreaser(Token):
    """A token that decreases the level of the current parser."""
    def changeState(self, state):
        state.dec()

class Leaver(Token):
    """A token that leaves the current parser."""
    def changeState(self, state):
        state.leave()


# some generic types:
class Space(Token): rx = r'\s+'
class Newline(Token): rx = r'\n'


# some base types that should be inherited:
class CommentBase(Token): pass
class StringBase(Token): pass
class EscapeBase(Token): pass
class NumericBase(Token): pass
class ErrorBase(Token): pass


# some mixin classes that make special handling of tokens possible besides correct parsing:

# MatchEnd and MatchStart can be used by parenthesis/brace matcher.
# the matchname class attribute defines the type, so that it is independent
# of the way other types could be nested.
class MatchStart: matchname="" # denotes that a Token matches another one,
class MatchEnd:   matchname="" # e.g. matching braces or parentheses


# Parsers:
class Parser(object):
    """Abstract base class for parsers.  Must be subclassed."""
    __metaclass__ = _makePatternMeta
    argcount = 0
    default = Unparsed
    
    def __init__(self, argcount = None):
        self.level = 0
        if argcount is not None:
            self.argcount = argcount

    def parse(self, text, pos):
        return self.pattern.search(text, pos)

    def fallthrough(self, state):
        """Called when no match is returned by parse().
        
        If this function returns True, the tokenizer stops parsing, assuming all
        text has been consumed.  If this function returns False or None, it
        should alter the state (switch parsers) and parsing continues using the
        new Parser.
        
        The default implementation simply returns True.
        
        """
        return True


class FallthroughParser(Parser):
    """Base class for parsers that 'match' instead of 'search' for a pattern.
    
    You should also implement the fallthrough() method to do something with
    the state if there is no match. See Parser().
    
    """
    def parse(self, text, pos):
        return self.pattern.match(text, pos)
    

class StringParserBase(Parser):
    """A Base class for parsers that parse quoted strings."""
    defaultClass = StringBase




def guessState(text):
    """Tries to guess the type of the input text.
    
    Returns the state class that can be used to parse it.
    
    """
    return {
        'lilypond': lilypond.LilyPondToplevelParser,
        'scheme':   scheme.SchemeParser,
        'docbook':  docbook.DocBookParser,
        'latex':    latex.LaTeXParser,
        'texi':     texi.TexinfoParser,
        'html':     html.HTMLParser,
        }[guessType(text)]
        


import lilypond
import scheme
import docbook
import latex
import texi
import html

