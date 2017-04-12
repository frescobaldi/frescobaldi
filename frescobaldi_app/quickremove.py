# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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


import functools

import lydocument
import ly.document
import ly.words
import ly.lex.lilypond


def remove(func):
    """Decorator turning a function yielding ranges into removing the ranges.

    Note that you should call the function with a QTextCursor as the first
    argument. The returned decorator converts the QTextCursor to a
    ly.document.Cursor, calls the function and removes the ranges returned
    by the function.

    """
    @functools.wraps(func)
    def decorator(cursor, *args):
        c = lydocument.cursor(cursor)
        remove = func(c, *args)
        with c.document as d:
            for start, end in remove:
                del d[start:end]
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
    source = ly.document.Source(cursor, None, ly.document.PARTIAL, True)
    for t in source:
        if isinstance(t, ly.lex.lilypond.Direction):
            start = t.pos
            for t in source.tokens:
                if isinstance(t, ly.lex.Space):
                    continue
                elif predicate_dir(t):
                    yield start, t.end
                break
        elif predicate(t):
            yield t.pos, t.end


@remove
def comments(cursor):
    """Remove all comments from the cursor's selection."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    for token in source:
        if isinstance(token, ly.lex.Comment):
            yield token.pos, token.end


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
def beams(cursor):
    """Remove beams from the cursor's selection."""
    return find_positions(cursor, lambda t: isinstance(t, ly.lex.lilypond.Beam))


@remove
def ligatures(cursor):
    """Remove ligatures from the cursor's selection."""
    return find_positions(cursor, lambda t: isinstance(t, ly.lex.lilypond.Ligature))


@remove
def dynamics(cursor):
    """Remove dynamics from the cursor's selection."""
    return find_positions(cursor, lambda t: isinstance(t, ly.lex.lilypond.Dynamic))


@remove
def fingerings(cursor):
    """Remove fingerings from the cursor's selection."""
    return find_positions(cursor, lambda t: isinstance(t, ly.lex.lilypond.Fingering))


@remove
def markup(cursor):
    """Remove (postfix) markup texts from the cursor's selection."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    for token in source:
        if isinstance(token, ly.lex.lilypond.Direction):
            start = token.pos
            for token in source:
                if token == '\\markup':
                    # find the end of the markup expression
                    depth = source.state.depth()
                    for token in source:
                        if source.state.depth() < depth:
                            yield start, token.end
                            break
                elif token == '"':
                    # find the end of the string
                    for token in source:
                        if isinstance(token, ly.lex.StringEnd):
                            yield start, token.end
                            break
                elif token.isalpha():
                    yield start, token.end
                elif isinstance(token, ly.lex.Space):
                    continue
                break


@remove
def smart_delete(cursor, backspace=False):
    r"""This function intelligently deletes an item the cursor is at.

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


