# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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

All functions except a ly.document.Cursor with the selected range.

"""

from __future__ import unicode_literals

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


def music_tokens(source, command=False, chord=False):
    """Yield lists of tokens describing rests, skips or pitches.
    
    source is a ly.document.Source instance following the state.
    
    The following keyword arguments can be used:
    - command: whether to allow pitches in \relative, \transpose, etc.
    - chord: whether to allow pitches inside chords.
    
    """
    skip_parsers = ()
    if not command:
        skip_parsers += (ly.lex.lilypond.ParsePitchCommand,)
    if not chord:
        skip_parsers += (ly.lex.lilypond.ParseChord,)

    for token in source:
        if isinstance(source.state.parser(), skip_parsers):
            continue
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
    
    
_start = (
    ly.lex.lilypond.Rest,
    ly.lex.lilypond.Skip,
    ly.lex.lilypond.Note,
    ly.lex.lilypond.ChordEnd,
    ly.lex.lilypond.Octave,
    ly.lex.lilypond.Accidental,
    ly.lex.lilypond.OctaveCheck,
    ly.lex.lilypond.Duration,
)

_stay = _start[4:]


def duration_tokens(source, *classes):
    """Yield lists of tokens where tokens in list are instance of *classes."""
    for tokens in music_tokens(source):
        yield [token for token in tokens if isinstance(token, classes)]

def duration_tokens_pos(source, *classes):
    """Yield tuples(pos, list of tokens) where tokens in list are instance of *classes.
    
    The list of tokens can be empty, the pos points to where a duration could be
    inserted.
    
    """
    for tokens in music_tokens(source):
        dur_tokens = [token for token in tokens if isinstance(token, classes)]
        pos = dur_tokens[0].pos if dur_tokens else tokens[-1].end
        yield pos, dur_tokens

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
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for tokens in duration_tokens(source, ly.lex.lilypond.Length):
            for token in tokens:
                try:
                    i = durations.index(token)
                except ValueError:
                    continue
                if i > 0:
                    d[token.pos:token.end] = durations[i - 1]

def rhythm_halve(cursor):
    """Halves all duration values."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for tokens in duration_tokens(source, ly.lex.lilypond.Length):
            for token in tokens:
                try:
                    i = durations.index(token)
                except ValueError:
                    continue
                if i < len(durations) - 1:
                    d[token.pos:token.end] = durations[i + 1]

def rhythm_dot(cursor):
    """Add a dot to all durations."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for tokens in duration_tokens(source, ly.lex.lilypond.Length):
            for token in tokens:
                d[token.end:token.end] = "."

def rhythm_undot(cursor):
    """Remove one dot from all durations."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for tokens in duration_tokens(source, ly.lex.lilypond.Dot):
            if tokens:
                del d[tokens[0].pos:tokens[0].end]

def rhythm_remove_scaling(cursor):
    """Remove the scaling (*3, *1/3) from all durations."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for tokens in duration_tokens(source, ly.lex.lilypond.Scaling):
            for token in tokens:
                del d[token.pos:token.end]
            
def rhythm_remove_fraction_scaling(cursor):
    """Remove the scaling containing fractions (*1/3) from all durations."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for tokens in duration_tokens(source, ly.lex.lilypond.Scaling):
            for token in tokens:
                if '/' in token:
                    del d[token.pos:token.end]

def rhythm_remove(cursor):
    """Remove all durations."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for tokens in duration_tokens(source, ly.lex.lilypond.Duration):
            if tokens:
                del d[tokens[0].pos:tokens[-1].end]

def rhythm_implicit(cursor):
    """Remove reoccurring durations."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    dtokens = duration_tokens(source, ly.lex.lilypond.Duration)
    for tokens in dtokens:
        break
    else:
        return
    prev = tokens or preceding_duration(cursor)
    with cursor.document as d:
        for tokens in dtokens:
            if tokens:
                if tokens == prev:
                    del d[tokens[0].pos:tokens[-1].end]
                prev = tokens

def rhythm_implicit_per_line(cursor):
    """Remove reoccurring durations, but always write one on a new line."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    dtokens = duration_tokens_pos(source, ly.lex.lilypond.Duration)
    for pos, tokens in dtokens:
        break
    else:
        return
    previous_block = source.block
    prev = tokens or preceding_duration(cursor)
    with cursor.document as d:
        for pos, tokens in dtokens:
            block = d.block(pos)
            if block != previous_block:
                if not tokens:
                    d[pos:pos] = ''.join(prev)
                else:
                    prev = tokens
                previous_block = block
            elif tokens:
                if tokens == prev:
                    del d[tokens[0].pos:tokens[-1].end]
                prev = tokens

def rhythm_explicit(cursor):
    """Make all durations explicit."""
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    dtokens = duration_tokens_pos(source, ly.lex.lilypond.Duration)
    for pos, tokens in dtokens:
        break
    else:
        return
    prev = tokens or preceding_duration(cursor)
    with cursor.document as d:
        for pos, tokens in dtokens:
            if tokens:
                prev = tokens
            else:
                d[pos:pos] = ''.join(prev)

def rhythm_overwrite(cursor, durations):
    """Apply a list of durations to the cursor's range.
    
    The durations list looks like ["4", "8", "", "16.",] etc.
    
    """
    durations_source = remove_dups(itertools.cycle(durations))
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for pos, tokens in duration_tokens_pos(source, ly.lex.lilypond.Duration):
            end = tokens[-1].end if tokens else pos
            d[pos:end] = next(durations_source)

def rhythm_extract(cursor):
    """Return a list of the durations from the cursor's range."""
    source = ly.document.Source(cursor, True)
    durations = list(duration_tokens(source, ly.lex.lilypond.Duration))
    # if the first duration was not given, find it
    if durations and not durations[0]:
        durations[0] = preceding_duration(cursor) or ['4']
    return ["".join(tokens) for tokens in durations]

