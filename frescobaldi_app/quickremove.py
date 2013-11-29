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
    def decorator(cursor, *args):
        remove = list(func(cursor, *args))
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


def is_instrument_script(token):
    """Return True if token is an instrument script."""
    return (isinstance(token, ly.lex.lilypond.Articulation)
            and token[1:] in ly.words.instrument_scripts)


def find_positions(cursor, predicate, predicate_dir=None):
    """Yields positions (start, end) for tokens predicate returns True for.
    
    The tokens (gotten from the cursor's selection) may be preceded by a
    ly.lex.lilypond.Direction token.
    If predicate_dir is specified, it is used for the items following a
    Direction tokens, otherwise predicate is also used for that case.
    
    """
    if predicate_dir is None:
        predicate_dir = predicate
    for block, tokens in tokeniter.selection(cursor, None, False):
        position = block.position()
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Direction):
                start = position + t.pos
                for t in tokens:
                    if isinstance(t, ly.lex.Space):
                        continue
                    elif predicate_dir(t):
                        yield start, position + t.end
                    break
            elif predicate(t):
                yield position + t.pos, position + t.end


@remove
def articulations(cursor):
    """Remove articulations from the cursor's selection."""
    return find_positions(cursor, is_articulation,
        lambda t: isinstance(t, ly.lex.lilypond.ScriptAbbreviation) or is_articulation(t))


@remove
def ornaments(cursor):
    """Remove ornaments from the cursor's selection."""
    return find_positions(cursor, is_ornament)


@remove
def instrument_scripts(cursor):
    """Remove instrument_scripts from the cursor's selection."""
    return find_positions(cursor, is_instrument_script)


@remove
def slurs(cursor):
    """Remove slurs from the cursor's selection."""
    return find_positions(cursor, lambda t: isinstance(t, ly.lex.lilypond.Slur))


@remove
def dynamics(cursor):
    """Remove dynamics from the cursor's selection."""
    return find_positions(cursor, lambda t: isinstance(t, ly.lex.lilypond.Dynamic))


@remove
def markup(cursor):
    """Remove (postfix) markup texts from the cursor's selection."""
    source = tokeniter.Source.selection(cursor, True, False)
    for token in source:
        if isinstance(token, ly.lex.lilypond.Direction):
            start = source.position(token)
            for token in source:
                if token == '\\markup':
                    # find the end of the markup expression
                    depth = source.state.depth()
                    for token in source:
                        if source.state.depth() < depth:
                            end = token.end + source.block.position()
                            yield start, end
                            break
                elif token == '"':
                    # find the end of the string
                    for token in source:
                        if isinstance(token, ly.lex.StringEnd):
                            end = token.end + source.block.position()
                            yield start, end
                            break
                elif token.isalpha():
                    end = token.end + source.block.position()
                    yield start, end
                elif isinstance(token, ly.lex.Space):
                    continue
                break


@remove
def smart_delete(cursor, backspace=False):
    """This function intelligently deletes an item the cursor is at.
    
    Basically it behaves like normal Delete (cursor.deleteChar()) or BackSpace
    (cursor.deletePreviousChar()), but it performs the following:
    
    - if the item is a matching object (, ), [, ], \[, \] etc, the other item is
      deleted as well
    - if the item is an articulation it is deleted completely with direction
      specifier if present
    - if the cursor is on a note, the whole notename is deleted including
      postfix stuff
    - if the cursor is on the '<' of a chord, the whole chord is deleted
    
    TODO: implement
    """
    pass


