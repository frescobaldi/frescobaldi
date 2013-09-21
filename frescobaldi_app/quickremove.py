# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
Remove certain types of LilyPond input from selected regions.

The functions are called by actions defined in the documentactions.py module.

"""

from __future__ import unicode_literals

import functools

from PyQt4.QtGui import QTextCursor

import tokeniter
import cursortools
import ly.words
import ly.lex.lilypond


def remove(func):
    """Decorator turning a function yielding ranges into removing the ranges."""
    @functools.wraps(func)
    def decorator(cursor):
        remove = list(func(tokeniter.selection(cursor, None, False)))
        if remove:
            c = QTextCursor(cursor)
            with cursortools.compress_undo(c):
                for start, end in sorted(remove, reverse=True):
                    c.setPosition(start)
                    c.setPosition(end, QTextCursor.KeepAnchor)
                    c.removeSelectedText()
    return decorator


def is_articulation(token):
    """Return True if token is an articulation."""
    return (isinstance(token, ly.lex.lilypond.Articulation)
            and token[1:] in ly.words.articulations)


def is_ornament(token):
    """Return True if token is an ornament."""
    return (isinstance(token, ly.lex.lilypond.Articulation)
            and token[1:] in ly.words.ornaments)

@remove
def articulations(source):
    """Remove articulations from the cursor's selection."""
    for block, tokens in source:
        position = block.position()
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Direction):
                start = position + t.pos
                for t in tokens:
                    if isinstance(t, ly.lex.Space):
                        continue
                    elif isinstance(t, ly.lex.lilypond.ScriptAbbreviation):
                        yield start, position + t.end
                    elif is_articulation(t):
                        yield start, position + t.end
                    break
            elif is_articulation(t):
                yield position + t.pos, position + t.end


@remove
def ornaments(source):
    """Remove ornaments from the cursor's selection."""
    for block, tokens in source:
        position = block.position()
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Direction):
                start = position + t.pos
                for t in tokens:
                    if isinstance(t, ly.lex.Space):
                        continue
                    elif is_ornament(t):
                        yield start, position + t.end
                    break
            elif is_ornament(t):
                yield position + t.pos, position + t.end


@remove
def slurs(source):
    """Remove slurs from the cursor's selection."""
    for block, tokens in source:
        position = block.position()
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Direction):
                start = position + t.pos
                for t in tokens:
                    if isinstance(t, ly.lex.Space):
                        continue
                    elif isinstance(t, ly.lex.lilypond.Slur):
                        yield start, position + t.end
                    break
            elif isinstance(t, ly.lex.lilypond.Slur):
                yield position + t.pos, position + t.end


@remove
def dynamics(source):
    """Remove dynamics from the cursor's selection."""
    for block, tokens in source:
        position = block.position()
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Direction):
                start = position + t.pos
                for t in tokens:
                    if isinstance(t, ly.lex.Space):
                        continue
                    elif isinstance(t, ly.lex.lilypond.Dynamic):
                        yield start, position + t.end
                    break
            elif isinstance(t, ly.lex.lilypond.Dynamic):
                yield position + t.pos, position + t.end


