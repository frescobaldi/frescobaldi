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
Convert relative music to absolute music.
"""

from __future__ import unicode_literals

import itertools

import ly.lex.lilypond


def rel2abs(cursor):
    """Converts pitches from relative to absolute."""
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
                relative(t)
                t = next(psource)
            elif isinstance(t, ly.lex.lilypond.MarkupScore):
                consume()
                t = next(psource)
            return t
        
        next = __next__
            
    tsource = gen()
    
    def makeAbsolute(p, lastPitch):
        """Makes pitch absolute (honoring and removing possible octaveCheck)."""
        if p.octavecheck is not None:
            p.octave = p.octavecheck
            p.octavecheck = None
        else:
            p.makeAbsolute(lastPitch)
        pitches.write(p)
    
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
    
    def relative(t):
        pos = t.pos
        lastPitch = None
        
        t = next(tsource)
        if isinstance(t, ly.pitch.Pitch):
            lastPitch = t
            t = next(tsource)
        else:
            lastPitch = ly.pitch.Pitch.c1()
        
        # remove the \relative <pitch> tokens
        del document[pos:t.pos]
        
        while True:
            # eat stuff like \new Staff == "bla" \new Voice \notes etc.
            if isinstance(source.state.parser(), ly.lex.lilypond.ParseTranslator):
                t = consume()
            elif isinstance(t, (ly.lex.lilypond.ChordMode, ly.lex.lilypond.NoteMode)):
                t = next(tsource)
            else:
                break
        
        # now convert the relative expression to absolute
        if t in ('{', '<<'):
            # Handle full music expression { ... } or << ... >>
            for t in context():
                # skip commands with pitches that do not count
                if isinstance(t, ly.lex.lilypond.PitchCommand):
                    if t == '\\octaveCheck':
                        pos = t.pos
                        for p in getpitches(context()):
                            # remove the \octaveCheck
                            lastPitch = p
                            end = (p.accidental_token or p.octave_token or p.note_token).end
                            del document[pos:end]
                            break
                    else:
                        consume()
                elif isinstance(t, ly.lex.lilypond.ChordStart):
                    # handle chord
                    chord = [lastPitch]
                    for p in getpitches(context()):
                        makeAbsolute(p, chord[-1])
                        chord.append(p)
                    lastPitch = chord[:2][-1] # same or first
                elif isinstance(t, ly.pitch.Pitch):
                    makeAbsolute(t, lastPitch)
                    lastPitch = t
        elif isinstance(t, ly.lex.lilypond.ChordStart):
            # Handle just one chord
            for p in getpitches(context()):
                makeAbsolute(p, lastPitch)
                lastPitch = p
        elif isinstance(t, ly.pitch.Pitch):
            # Handle just one pitch
            makeAbsolute(t, lastPitch)
    
    # Do it!
    with cursor.document as document:
        for t in tsource:
            pass


