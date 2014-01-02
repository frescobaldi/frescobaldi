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

r"""
This module is built on top of slexer and can parse LilyPond input and other
formats.

The base functionality is delegated to modules with an underscore in this package.
The modules describing parsing modes (filetypes) are the files without underscore.

Currently available are modes for lilypond, latex, html, texinfo, scheme, and docbook.

The 'underscored' modules should not be imported in application code. What is
needed from them is available here, in the ly.lex namespace.

If you add new files for parsing other file types, you should add them in _mode.py.
The _token.py module contains base Token types and Token mixin classes.

The State, Parser, FallthroughParser and Fridge classes from slexer are all
slightly extended here,

Usage:

>>> import ly.lex
>>> txt = r"\relative c' { c d e f-^ g }"
>>> s = ly.lex.state("lilypond")
>>> for t in s.tokens(txt):
...     print t, t.__class__.__name__

\relative Command
  Space
c Name
' Unparsed
  Space
{ SequentialStart
  Space
c Note
  Space
d Note
  Space
e Note
  Space
f Note
- Direction
^ ScriptAbbreviation
  Space
g Note
  Space
} SequentialEnd

A State() is used to parse text. The text is given to the tokens() method, that
returns an iterator iterating over Token instances as they are found. Each token
has a 'pos' and an 'end' attribute describing its position in the original
string.

While iterating over the tokens(), the State maintains information about what
kind of text is parsed. (So don't iterate over more than one call to tokens() of
the same State object at the same time.)

Use ly.lex.state("name") to get a state for a specific mode to start parsing with.
If you don't know the type of text, you can use ly.lex.guessState(text), where
text is the text you want to parse. A quick heuristic is then used to determine
the type of the text.

See for more information the documentation of the slexer module.

"""

from __future__ import unicode_literals

import re

import slexer
from ._token import *
from ._mode import extensions, modes, guessMode


__all__ = [
    'State',
    'Parser', 'FallthroughParser',
    'Fridge',
    'extensions', 'modes', 'guessMode',
    'state', 'guessState',
    'Token',
    'Unparsed',
    'Space',
    'Newline',
    'Comment',
    'LineComment',
    'BlockComment',
    'BlockCommentStart',
    'BlockCommentEnd',
    'String',
    'StringStart',
    'StringEnd',
    'Character',
    'Numeric',
    'Error',
    'MatchStart',
    'MatchEnd',
    'Indent',
    'Dedent',
]


class Parser(slexer.Parser):
    re_flags = re.MULTILINE | re.UNICODE
    argcount = 0
    default = Unparsed
    mode = None
    
    def __init__(self, argcount = None):
        if argcount is not None:
            self.argcount = argcount

    def freeze(self):
        return (self.argcount,)


class FallthroughParser(Parser, slexer.FallthroughParser):
    pass


class State(slexer.State):
    def endArgument(self):
        """Decrease argcount and leave the parser if it would reach 0."""
        while self.depth() > 1:
            p = self.parser()
            if p.argcount == 1:
                self.leave()
            else:
                if p.argcount > 0:
                    p.argcount -= 1
                return
    
    def mode(self):
        """Returns the mode attribute of the first parser (from current parser) that has it."""
        for parser in self.state[::-1]:
            if parser.mode:
                return parser.mode


class Fridge(slexer.Fridge):
    def __init__(self, stateClass = State):
        super(Fridge, self).__init__(stateClass)


def state(mode):
    """Returns a State instance for the given mode."""
    return State(modes[mode]())


def guessState(text):
    """Returns a State instance, guessing the type of text."""
    return State(modes[guessMode(text)]())


