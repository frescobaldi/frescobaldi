# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2011 - 2015 by Wilbert Berendsen
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
Implementation of the tools to edit durations of selected music.

Durations are represented simply by lists of ly.lex.lilypond.Duration tokens.

All functions expect a ly.document.Cursor with the selected range.

"""

from __future__ import unicode_literals

import collections
import itertools

import ly.document
import ly.lex.lilypond


durations = ['\\maxima', '\\longa', '\\breve',
    '1', '2', '4', '8', '16', '32', '64', '128', '256', '512', '1024', '2048']


def remove_dups(iterable):
    """Change reoccurring strings to '' in iterable."""
    old = None
    for i in iterable:
        yield '' if i == old else i
        old = i

# describes a musical item that has a duration
music_item = collections.namedtuple('music_item', (
    'tokens',       # tokens of the item
    'dur_tokens',   # Duration tokens of the item
    'may_remove',   # whether the duration may be removed
    'insert_pos',   # where a Duration could be inserted
    'pos',          # position of the first token
    'end',          # end position of the last token
))

_start = (
    ly.lex.lilypond.Rest,
    ly.lex.lilypond.Skip,
    ly.lex.lilypond.Note,
    ly.lex.lilypond.ChordEnd,
    ly.lex.lilypond.Q,
    ly.lex.lilypond.Octave,
    ly.lex.lilypond.Accidental,
    ly.lex.lilypond.OctaveCheck,
    ly.lex.lilypond.Duration,
    ly.lex.lilypond.Tempo,
    ly.lex.lilypond.Partial
)

_stay = (
    ly.lex.lilypond.Octave,
    ly.lex.lilypond.Accidental,
    ly.lex.lilypond.OctaveCheck,
    ly.lex.lilypond.Duration,
    ly.lex.lilypond.Tie,
)

def music_tokens(source, command=False, chord=False):
    r"""DEPRECATED. Yield lists of tokens describing rests, skips or pitches.

    source is a ly.document.Source instance following the state.

    The following keyword arguments can be used:

    - command: whether to allow pitches in \\relative, \\transpose, etc.
    - chord: whether to allow pitches inside chords.

    This function is deprecated and will be removed.
    You should use music_items() instead.

    """
    skip_parsers = ()
    if not command:
        skip_parsers += (ly.lex.lilypond.ParsePitchCommand,)
    if not chord:
        skip_parsers += (ly.lex.lilypond.ParseChord,)

    for token in source:
        if isinstance(source.state.parser(), skip_parsers):
            continue
        # make sure to skip the duration tokens in a \tuplet command
        if token == '\\tuplet':
            for token in source:
                if isinstance(token, ly.lex.lilypond.Duration):
                    for token in source:
                        if not isinstance(token, ly.lex.lilypond.Duration):
                            break
                    break
                elif not isinstance(token, (ly.lex.Space, ly.lex.Numeric)):
                    break

        while isinstance(token, _start):
            l = [token]
            for token in source:
                if isinstance(token, ly.lex.Space):
                    continue
                if not isinstance(token, _stay):
                    yield l
                    break
                l.append(token)
            else:
                yield l
                break

def music_items(cursor, command=False, chord=False, partial=ly.document.INSIDE):
    r"""Yield music_item instances describing rests, skips or pitches.

    cursor is a ly.document.Cursor instance.

    The following keyword arguments can be used:

    - command: whether to allow pitches in \\relative, \\transpose, etc.
    - chord: whether to allow pitches inside chords.
    - partial: ly.document.INSIDE (default), PARTIAL or OUTSIDE.
      See the documentation of ly.document.Source.__init__().

    """
    skip_parsers = ()
    if not command:
        skip_parsers += (ly.lex.lilypond.ParsePitchCommand,)
    if not chord:
        skip_parsers += (ly.lex.lilypond.ParseChord,)

    source = ly.document.Source(cursor, True, partial=partial, tokens_with_position=True)

    def mk_item(l):
        """Convert a list of tokens to a music_item instance."""
        tokens = []
        dur_tokens = []
        pos = l[0].pos
        end = l[-1].end
        for t in l:
            if isinstance(t, ly.lex.lilypond.Duration):
                dur_tokens.append(t)
            else:
                tokens.append(t)
        may_remove = not any(map(('\\skip', '\\tempo', '\\tuplet', '\\partial').__contains__, tokens))
        if dur_tokens:
            insert_pos = dur_tokens[0].pos
        else:
            for t in reversed(tokens):
                if not isinstance(t, ly.lex.lilypond.Tie):
                    break
            insert_pos = t.end
        return music_item(tokens, dur_tokens, may_remove, insert_pos, pos, end)

    for token in source:
        if isinstance(source.state.parser(), skip_parsers):
            continue
        # make sure to skip the duration tokens in a \tuplet command
        if token == '\\tuplet':
            l = [token]
            for token in source:
                if isinstance(token, ly.lex.lilypond.Duration):
                    l.append(token)
                    for token in source:
                        if not isinstance(token, ly.lex.lilypond.Duration):
                            break
                        l.append(token)
                    break
                elif isinstance(token, ly.lex.Numeric):
                    l.append(token)
                elif not isinstance(token, ly.lex.Space):
                    break
            yield mk_item(l)

        length_seen = False
        while isinstance(token, _start):
            l = [token]
            if isinstance(token, ly.lex.lilypond.Length):
                length_seen = True
            for token in source:
                if isinstance(token, ly.lex.lilypond.Length):
                    if length_seen is True:
                        yield mk_item(l)
                        length_seen = False
                        break
                    else:
                        length_seen = True
                elif isinstance(token, ly.lex.Space):
                    continue
                elif isinstance(token, ly.lex.lilypond.ChordSeparator):
                    # prevent seeing the g in e.g. chordmode { c/g }
                    for token in source:
                        if not isinstance(token, (ly.lex.Space, ly.lex.lilypond.Note)):
                            break
                    continue
                elif not isinstance(token, _stay):
                    yield mk_item(l)
                    length_seen = False
                    break
                l.append(token)
            else:
                yield mk_item(l)
                break

def preceding_duration(cursor):
    """Return a preceding duration before the cursor, or an empty list."""
    tokens = ly.document.Runner.at(cursor).backward()
    for t in tokens:
        if isinstance(t, ly.lex.lilypond.Duration):
            l = [t]
            for t in tokens:
                if isinstance(t, ly.lex.lilypond.Duration):
                    l.append(t)
                elif not isinstance(t, ly.lex.Space):
                    break
            l.reverse()
            return l
    return []

def rhythm_double(cursor):
    """Doubles all duration values."""
    with cursor.document as d:
        for item in music_items(cursor):
            for token in item.dur_tokens:
                if isinstance(token, ly.lex.lilypond.Length):
                    try:
                        i = durations.index(token)
                    except ValueError:
                        pass
                    else:
                        if i > 0:
                            d[token.pos:token.end] = durations[i - 1]
                    break

def rhythm_halve(cursor):
    """Halves all duration values."""
    with cursor.document as d:
        for item in music_items(cursor):
            for token in item.dur_tokens:
                if isinstance(token, ly.lex.lilypond.Length):
                    try:
                        i = durations.index(token)
                    except ValueError:
                        pass
                    else:
                        if i < len(durations) - 1:
                            d[token.pos:token.end] = durations[i + 1]
                    break

def rhythm_dot(cursor):
    """Add a dot to all durations."""
    with cursor.document as d:
        for item in music_items(cursor):
            for token in item.dur_tokens:
                if isinstance(token, ly.lex.lilypond.Length):
                    d[token.end:token.end] = "."
                    break

def rhythm_undot(cursor):
    """Remove one dot from all durations."""
    with cursor.document as d:
        for item in music_items(cursor):
            for token in item.dur_tokens:
                if isinstance(token, ly.lex.lilypond.Dot):
                    del d[token.pos:token.end]
                    break

def rhythm_remove_scaling(cursor):
    """Remove the scaling (like ``*3``, ``*1/3``) from all durations."""
    with cursor.document as d:
        for item in music_items(cursor):
            for token in item.dur_tokens:
                if isinstance(token, ly.lex.lilypond.Scaling):
                    del d[token.pos:token.end]

def rhythm_remove_fraction_scaling(cursor):
    """Remove the scaling containing fractions (like ``*1/3``) from all durations."""
    with cursor.document as d:
        for item in music_items(cursor):
            for token in item.dur_tokens:
                if isinstance(token, ly.lex.lilypond.Scaling) and '/' in token:
                    del d[token.pos:token.end]

def rhythm_remove(cursor):
    """Remove all durations."""
    with cursor.document as d:
        for item in music_items(cursor):
            if item.dur_tokens and item.may_remove:
                del d[item.dur_tokens[0].pos:item.dur_tokens[-1].end]

def rhythm_implicit(cursor):
    """Remove reoccurring durations."""
    items = music_items(cursor)
    for item in items:
        break
    else:
        return
    if set(item.tokens) & set(('\\tempo', '\\tuplet', '\\partial')):
        prev = None
    else:
        prev = item.dur_tokens or preceding_duration(cursor)
    with cursor.document as d:
        for item in items:
            if not set(item.tokens) & set(('\\tempo', '\\tuplet', '\\partial')):
                if item.dur_tokens:
                    if item.dur_tokens == prev and item.may_remove:
                        del d[item.dur_tokens[0].pos:item.dur_tokens[-1].end]
                    prev = item.dur_tokens

def rhythm_implicit_per_line(cursor):
    """Remove reoccurring durations, but always write one on a new line."""
    items = music_items(cursor)
    for item in items:
        break
    else:
        return
    if set(item.tokens) & set(('\\tempo', '\\tuplet', '\\partial')):
        prev = None
    else:
        prev = item.dur_tokens or preceding_duration(cursor)
    if prev:
        previous_block = cursor.document.block(prev[0].pos)
    else:
        previous_block = None
    with cursor.document as d:
        for item in items:
            if not set(item.tokens) & set(('\\tempo', '\\tuplet', '\\partial')):
                block = d.block( (item.dur_tokens or item.tokens) [0].pos)
                if block != previous_block:
                    if not item.dur_tokens:
                        d[item.insert_pos:item.insert_pos] = ''.join(prev)
                    else:
                        prev = item.dur_tokens
                    previous_block = block
                elif item.dur_tokens:
                    if item.dur_tokens == prev and item.may_remove:
                        del d[item.dur_tokens[0].pos:item.dur_tokens[-1].end]
                    prev = item.dur_tokens

def rhythm_explicit(cursor):
    """Make all durations explicit."""
    items = music_items(cursor)
    for item in items:
        break
    else:
        return
    prev = item.dur_tokens or preceding_duration(cursor)
    with cursor.document as d:
        for item in items:
            if not set(item.tokens) & set(('\\tempo', '\\tuplet', '\\partial')):
                if item.dur_tokens:
                    prev = item.dur_tokens
                else:
                    d[item.insert_pos:item.insert_pos] = ''.join(prev)

def rhythm_overwrite(cursor, durations):
    """Apply a list of durations to the cursor's range.

    The durations list looks like ["4", "8", "", "16.",] etc.

    """
    durations_source = remove_dups(itertools.cycle(durations))
    with cursor.document as d:
        for item in music_items(cursor):
            pos = item.insert_pos
            end = item.dur_tokens[-1].end if item.dur_tokens else pos
            d[pos:end] = next(durations_source)

def rhythm_extract(cursor):
    """Return a list of the durations from the cursor's range."""
    source = ly.document.Source(cursor, True)
    durations = []
    for item in music_items(cursor):
        tokens = item.dur_tokens + [t for t in item.tokens if isinstance(t, ly.lex.lilypond.Tie)]
        durations.append(tokens)
    # if the first duration was not given, find it
    if durations and not durations[0]:
        durations[0] = preceding_duration(cursor) or ['4']
    return ["".join(tokens) for tokens in durations]

