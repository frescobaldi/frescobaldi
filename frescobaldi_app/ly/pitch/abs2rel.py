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
Convert absolute music to relative music.
"""

from __future__ import unicode_literals

import itertools

import ly.lex.lilypond


def abs2rel(cursor):
    """Converts pitches from absolute to relative."""
    start = cursor.start
    cursor.start = 0
    
    source = ly.document.Source(cursor, True, tokens_with_position=True)

    pitches = ly.pitch.PitchIterator(source)
    psource = pitches.pitches()
    
    if start > 0:
        # consume tokens before the selection, following the language
        t = source.consume(pitches.tokens(), start)
        if t:
            psource = itertools.chain((t,), psource)
    
    # this class dispatches the tokens. we can't use a generator function
    # as that doesn't like to be called again while there is already a body
    # running.
    class gen(object):
        def __iter__(self):
            return self
        
        def __next__(self):
            t = next(psource)
            while isinstance(t, (ly.lex.Space, ly.lex.Comment)):
                t = next(psource)
            if t == '\\relative' and isinstance(t, ly.lex.lilypond.Command):
                relative()
                t = next(psource)
            elif isinstance(t, ly.lex.lilypond.ChordMode):
                consume() # do not change chords
                t = next(psource)
            elif isinstance(t, ly.lex.lilypond.MarkupScore):
                consume()
                t = next(psource)
            return t
        
        next = __next__
            
    tsource = gen()

    def getpitches(iterable):
        """Consumes iterable but only yields Pitch instances."""
        for p in iterable:
            if isinstance(p, ly.pitch.Pitch):
                yield p

    def context():
        """Consume tokens till the level drops (we exit a construct)."""
        depth = source.state.depth()
        for t in tsource:
            yield t
            if source.state.depth() < depth:
                return
    
    def consume():
        """Consume tokens from context() returning the last token, if any."""
        t = None
        for t in context():
            pass
        return t
    
    def relative():
        """Consume the whole \relative expression without doing anything. """
        # skip pitch argument
        t = next(tsource)
        if isinstance(t, ly.pitch.Pitch):
            t = next(tsource)
        
        while True:
            # eat stuff like \new Staff == "bla" \new Voice \notes etc.
            if isinstance(source.state.parser(), ly.lex.lilypond.ParseTranslator):
                t = consume()
            elif isinstance(t, ly.lex.lilypond.NoteMode):
                t = next(tsource)
            else:
                break
        
        if t in ('{', '<<', '<'):
            consume()
    
    # Do it!
    with cursor.document as document:
        for t in tsource:
            if t in ('{', '<<'):
                # Ok, parse current expression.
                pos = t.pos     # where to insert the \relative command
                lastPitch = None
                chord = None
                for t in context():
                    # skip commands with pitches that do not count
                    if isinstance(t, ly.lex.lilypond.PitchCommand):
                        consume()
                    elif isinstance(t, ly.lex.lilypond.ChordStart):
                        # Handle chord
                        chord = []
                    elif isinstance(t, ly.lex.lilypond.ChordEnd):
                        if chord:
                            lastPitch = chord[0]
                        chord = None
                    elif isinstance(t, ly.pitch.Pitch):
                        # Handle pitch
                        if lastPitch is None:
                            lastPitch = ly.pitch.Pitch.c1()
                            lastPitch.octave = t.octave
                            if t.note > 3:
                                lastPitch.octave += 1
                            document[pos:pos] = "\\relative {0} ".format(
                                    lastPitch.output(pitches.language))
                        p = t.copy()
                        t.makeRelative(lastPitch)
                        pitches.write(t)
                        lastPitch = p
                        # remember the first pitch of a chord
                        if chord == []:
                            chord.append(p)


