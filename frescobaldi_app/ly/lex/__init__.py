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
This module can parse any input, although some functionality is inspired by the
different peculiarities of the LilyPond .LY format.

The base functionality is delegated to modules with an underscore in this package.
The modules describing parsing modes (filetypes) are the files without underscore.

Currently available are modes for lilypond, latex, html, texinfo, scheme, and docbook.

The 'underscored' modules should not be imported in application code, but accessed
directly from here.

If you add new files for parsing other file types, you should add them in _mode.py.
The _token.py module contains base Token types and Token mixin classes.
The _parser.py module contains the implementation of Parser and FallthroughParser.
The _base.py module contains State, the state maintainer with its tokens() function.

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
"""

from __future__ import unicode_literals


__all__ = [
    'State',
    'extensions', 'modes', 'guessMode',
    'state', 'guessState', 'thawState',
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


from _base import State
from _mode import extensions, modes, guessMode
from _token import *


def state(mode):
    """Returns a State instance for the given mode."""
    return State(modes[mode]())


def guessState(text):
    """Returns a State instance, guessing the type of text."""
    return State(modes[guessMode(text)]())


def thawState(frozen):
    """Unfreezes the given state."""
    return State.thaw(frozen)


