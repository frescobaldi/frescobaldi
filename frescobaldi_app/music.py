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
Accesses streams of tokens and interprets them as LilyPond music,
finds notes, chords, durations, looks for positions to add postfix commands,
etc.
"""

from __future__ import unicode_literals

import ly.lex.lilypond


def music_items(source, command=False, chord=False, tokens=None):
    """Yields lists of tokens describing rests, skips or pitches.
    
    source is a tokeniter.Source instance.
    
    The following keyword arguments can be used:
    
    command: whether to skip pitches in \relative, \transpose, etc.
    chord: whether to skip pitches inside chords.
    tokens: if given, it is used as main iterator instead of the source object.
    
    Each list is a contiguous group of tokens (at least one).
    All tokens in a list are on the same line (QTextBlock). The current block
    can be found in the block attribute of the used tokeniter.Source instance.
    
    This is a small limitation compared to LilyPond, which allows a pitch on
    one line and its duration on the next, but it makes it easier to iterate
    on tokens (which only know their position in the current block).
    
    """
    skip_parsers = ()
    if not command:
        skip_parsers += (ly.lex.lilypond.ParsePitchCommand,)
    if not chord:
        skip_parsers += (ly.lex.lilypond.ParseChord,)

    for t in tokens or source:
        if isinstance(source.state.parser(), skip_parsers):
            continue
        while isinstance(t, _start):
            l = [t]
            for t in source.tokens:
                if not isinstance(t, _stay):
                    yield l
                    break
                l.append(t)
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


