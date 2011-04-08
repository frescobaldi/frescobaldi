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
Various routines parsing LilyPond text.
"""

from __future__ import unicode_literals


import itertools

import ly.tokenize.lilypond
import ly.tokenize.scheme


def includeargs(tokens):
    """Yields the arguments of \\include commands in the token stream."""
    for token in tokens:
        if isinstance(token, ly.tokenize.lilypond.Keyword) and token == "\\include":
            for token in tokens:
                if not isinstance(token, (ly.tokenize.Space, ly.tokenize.Comment)):
                    break
            if token == '"':
                yield ''.join(itertools.takewhile(lambda t: t != '"', tokens))


def outputargs(tokens):
    """Yields the arguments of \\bookOutputName, \\bookOutputSuffix and define output-suffix commands.
    
    Every argument is a two tuple(type, argument) where type is either "suffix" or "name".
    
    """
    for token in tokens:
        found = None
        if isinstance(token, ly.tokenize.lilypond.Command):
            if token == "\\bookOutputName":
                found = "name"
            elif token == "\\bookOutputSuffix":
                found = "suffix"
        elif isinstance(token, ly.tokenize.scheme.Word) and token == "output-suffix":
            found = "suffix"
        if found:
            for token in tokens:
                if not isinstance(token, (ly.tokenize.lilypond.SchemeStart,
                                          ly.tokenize.Space,
                                          ly.tokenize.Comment)):
                    break
            if token == '"':
                yield found, ''.join(itertools.takewhile(lambda t: t != '"', tokens))


def version(tokens):
    """Returns the argument of \\version, if found in this token stream."""
    for token in tokens:
        if isinstance(token, ly.tokenize.lilypond.Keyword) and token == "\\version":
            for token in tokens:
                if not isinstance(token, (ly.tokenize.Space, ly.tokenize.Comment)):
                    break
            if token == '"':
                pred = lambda t: t != '"'
            else:
                pred = lambda t: not isinstance(t, ly.tokenize.Space, ly.tokenize.Comment)
            return ''.join(itertools.takewhile(pred, tokens))


