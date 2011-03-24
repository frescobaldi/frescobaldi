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

from __future__ import unicode_literals

"""
Parses and tokenizes LilyPond input.

Also supports LilyPond embedded in HTML, LaTeX, DocBook and Scheme embedded in
LilyPond (and vice versa).

Much functionality is delegated to modules with an underscore in this package.
The modules describing parsing modes (filetypes) are the files without underscore.

The 'underscored' modules should not be used in application code.
All important classes or functions are available here.

In _mode.py you should register new mode files.
The _token.py module contains base Token types and Token mixin classes.
The _parser.py module contains the implementation of Parser and FallthroughParser.
The _base.py module contains State, the state maintainer with its tokens() function.

"""


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


