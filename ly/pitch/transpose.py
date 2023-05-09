# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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
Transposing music.
"""

from __future__ import unicode_literals

from fractions import Fraction

import ly.lex.lilypond


class Transposer(object):
    """Transpose pitches.
    
    Instantiate with a from- and to-Pitch, and optionally a scale.
    The scale is a list with the pitch height of the unaltered step (0 .. 6).
    The default scale is the normal scale: C, D, E, F, G, A, B.
    
    """
    scale = (0, 1, 2, Fraction(5, 2), Fraction(7, 2), Fraction(9, 2), Fraction(11, 2))
        
    def __init__(self, fromPitch, toPitch, scale = None):
        if scale is not None:
            self.scale = scale
        
        # the number of octaves we need to transpose
        self.octave = toPitch.octave - fromPitch.octave
        
        # the number of base note steps (c->d == 1, e->f == 1, etc.)
        self.steps = toPitch.note - fromPitch.note
        
        # the number (fraction) of real whole steps
        self.alter = (self.scale[toPitch.note] + toPitch.alter -
                      self.scale[fromPitch.note] - fromPitch.alter)
                  
    def transpose(self, pitch):
        doct, note = divmod(pitch.note + self.steps, 7)
        pitch.alter += self.alter - doct * 6 - self.scale[note] + self.scale[pitch.note]
        pitch.octave += self.octave + doct
        pitch.note = note
        # change the step if alterations fall outside -1 .. 1
        while pitch.alter > 1:
            doct, note = divmod(pitch.note + 1, 7)
            pitch.alter -= doct * 6 + self.scale[note] - self.scale[pitch.note]
            pitch.octave += doct
            pitch.note = note
        while pitch.alter < -1:
            doct, note = divmod(pitch.note - 1, 7)
            pitch.alter += doct * -6 + self.scale[pitch.note] - self.scale[note]
            pitch.octave += doct
            pitch.note = note
            
            
class Simplifier(Transposer):
    """Make complicated accidentals simpler by substituting naturals where possible.
    
    """
    def __init__(self, scale=None):
        if scale is not None:
            self.scale = scale
    
    def transpose(self, pitch):
        if pitch.alter == 1:
            doct, note = divmod(pitch.note + 1, 7)
            pitch.alter -= doct * 6 + self.scale[note] - self.scale[pitch.note]
            pitch.octave += doct
            pitch.note = note
        elif pitch.alter == -1:
            doct, note = divmod(pitch.note - 1, 7)
            pitch.alter += doct * -6 + self.scale[pitch.note] - self.scale[note]
            pitch.octave += doct
            pitch.note = note
        if pitch.alter == Fraction(1, 2):
            doct, note = divmod(pitch.note + 1, 7)
            alter = doct * 6 + self.scale[note] - self.scale[pitch.note]
            if alter == Fraction(1, 2):
                pitch.alter = 0
                pitch.octave += doct
                pitch.note = note
        elif pitch.alter == Fraction(-1, 2):
            doct, note = divmod(pitch.note - 1, 7)
            alter = doct * -6 + self.scale[pitch.note] - self.scale[note]
            if alter == Fraction(1, 2):
                pitch.alter = 0
                pitch.octave += doct
                pitch.note = note


class ModeShifter(Transposer):
    """
    Shift pitches to optional mode/scale.
    
    The scale should be formatted in analogy to the scale in the Transposer
    parent class.
    
    The key should be an instance of ly.pitch.Pitch. 
    """
    def __init__(self, key, scale):
        """
        Create scale of pitches from given scale definition.
        """
        import math
        self.octave = 0
        self.modpitches = [0] * 7
        for s, a in scale:
            p = key.copy()
            self.steps = s 
            self.alter = a
            super(ModeShifter, self).transpose(p)
            if self.modpitches[p.note]:
                self.modpitches[p.note].append(p)
            else:
                self.modpitches[p.note] = [p]
        
    def closestPitch(self, pitch):
        """
        Get closest pitch from scale. 
        
        If only one scale note with the same base step exist that is returned.
        Otherwise the closest is calculated.
        """
        def getNextPitch(step, up=True):
            modepitch = self.modpitches[step]
            if modepitch:
                return modepitch
            else:
                if up:
                    step = (step + 1) % 7
                else:
                    step = (step - 1) % 7
                return getNextPitch(step, up)
                
        def comparePitch(pitch, uppitch, dwnpitch):
            upnum = self.scale[uppitch.note] + uppitch.alter
            dwnnum = self.scale[dwnpitch.note] + dwnpitch.alter
            pnum = self.scale[pitch.note] + pitch.alter
            if upnum - pnum < pnum - dwnnum:
                return uppitch
            else: 
                return dwnpitch
            
        step = pitch.note
        modepitch = self.modpitches[step]
        if modepitch and len(modepitch) == 2:
            return comparePitch(pitch, modepitch[0], modepitch[1])
        else:
            uppitch = getNextPitch(step)[0] 
            dwnpitch = getNextPitch(step, False)[-1]
            return comparePitch(pitch, uppitch, dwnpitch)
            
        
    def transpose(self, pitch):
        """
        Shift to closest scale pitch if not already in scale.
        """
        modpitch = self.modpitches[pitch.note]
        if modpitch:
            for mp in modpitch:
                if pitch.note == mp.note and pitch.alter == mp.alter:
                    return
        clp = self.closestPitch(pitch)
        self.steps = clp.note - pitch.note
        if self.steps > 3:
            self.octave = -1
        elif self.steps < -3:
            self.octave = 1
        else:
            self.octave = 0
        self.alter = (self.scale[clp.note] + clp.alter -
                      self.scale[pitch.note] - pitch.alter)
        super(ModeShifter, self).transpose(pitch)


class ModalTransposer(object):
    """Transpose pitches by number of steps within a given scale.
    
    Instantiate with the number of steps (+/-) in the scale to transpose by, and a mode index.
    The mode index is the index of the major scale in the circle of fifths (C Major = 0).
    """        
    def __init__(self, numSteps = 1, scaleIndex = 0):
        self.numSteps = numSteps
        self.notes = [0, 1, 2, 3, 4, 5, 6]
        self.alter = [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5]
        # Initialize to Db, then update to desired mode
        
        for i in range(0, scaleIndex):
            keyNameIndex = ((i+1)*4)%len(self.notes)
            accidentalIndex = (keyNameIndex-1)%len(self.notes)
            self.alter[accidentalIndex] += .5
            
    @staticmethod
    def getKeyIndex(text):
        """Get the index of the key in the circle of fifths.
        
        'Cb' returns 0, 'C' returns 7, 'B#' returns 14.
        """
        circleOfFifths = ['Cb', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F',
                          'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#']
        return circleOfFifths.index(text.capitalize())
                  
    def transpose(self, pitch):
        # Look for an exact match: otherwise,
        # look for the letter name and save the accidental
        for i in range(len(self.notes)):
            if pitch.note == self.notes[i] and pitch.alter == self.alter:
                fromScaleDeg = i
                accidental = 0
                break
        else:
            fromScaleDeg = self.notes.index(pitch.note)
            accidental = pitch.alter - self.alter[fromScaleDeg]
        
        toOctaveMod, toScaleDeg = divmod(fromScaleDeg + self.numSteps, 7)
        pitch.note = self.notes[toScaleDeg]
        pitch.alter = self.alter[toScaleDeg] + accidental
        pitch.octave += toOctaveMod


def transpose(cursor, transposer, language="nederlands", relative_first_pitch_absolute=False):
    """Transpose pitches using the specified transposer.
    
    If relative_first_pitch_absolute is True, the first pitch in a \\relative
    expression is considered to be absolute, when a startpitch is not given.
    This is LilyPond >= 2.18 behaviour.
    
    If relative_first_pitch_absolute is False, the first pitch in a \\relative
    expression is considered to be relative to c', is no startpitch is given.
    This is LilyPond < 2.18 behaviour.
    
    Currently, relative_first_pitch_absolute defaults to False.
    
    """
    start = cursor.start
    cursor.start = 0
    
    source = ly.document.Source(cursor, True, tokens_with_position=True)

    pitches = ly.pitch.PitchIterator(source, language)
    psource = pitches.pitches()

    class gen(object):
        def __iter__(self):
            return self
        
        def __next__(self):
            while True:
                t = next(psource)
                if isinstance(t, (ly.lex.Space, ly.lex.Comment)):
                    continue
                # Handle stuff that's the same in relative and absolute here
                if t == "\\relative":
                    relative()
                elif isinstance(t, ly.lex.lilypond.MarkupScore):
                    absolute(context())
                elif isinstance(t, ly.lex.lilypond.ChordMode):
                    chordmode()
                elif isinstance(t, ly.lex.lilypond.Command) and t == '\\stringTuning':
                    string_tuning()
                elif isinstance(t, ly.lex.lilypond.PitchCommand):
                    if t == "\\transposition":
                        next(psource) # skip pitch
                    elif t == "\\transpose":
                        for p in getpitches(context()):
                            transpose(p)
                    elif t == "\\key":
                        for p in getpitches(context()):
                            transpose(p, 0)
                    else:
                        return t
                else:
                    return t
        
        next = __next__
    
    tsource = gen()
    
    def in_selection(p):
        """Return True if the pitch or token p may be replaced, i.e. was selected."""
        return start == 0 or pitches.position(p) >= start
    
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
        
    def transpose(p, resetOctave = None):
        """Transpose absolute pitch, using octave if given."""
        transposer.transpose(p)
        if resetOctave is not None:
            p.octave = resetOctave
        if in_selection(p):
            pitches.write(p)

    def chordmode():
        r"""Called inside \chordmode or \chords."""
        for p in getpitches(context()):
            transpose(p, 0)
            
    def string_tuning():
        r"""Called after \stringTuning. Ignores the following chord expression."""
        for t in tsource:
            if isinstance(t, ly.lex.lilypond.ChordStart):
                consume()
            break
    
    def absolute(tokens):
        r"""Called when outside a possible \relative environment."""
        for p in getpitches(tokens):
            transpose(p)
    
    def relative():
        r"""Called when \relative is encountered."""
        def transposeRelative(p, lastPitch):
            """Transposes a relative pitch; returns the pitch in absolute form."""
            # absolute pitch determined from untransposed pitch of lastPitch
            p.makeAbsolute(lastPitch)
            if not in_selection(p):
                return p
            # we may change this pitch. Make it relative against the
            # transposed lastPitch.
            try:
                last = lastPitch.transposed
            except AttributeError:
                last = lastPitch
            # transpose a copy and store that in the transposed
            # attribute of lastPitch. Next time that is used for
            # making the next pitch relative correctly.
            newLastPitch = p.copy()
            transposer.transpose(p)
            newLastPitch.transposed = p.copy()
            if p.octavecheck is not None:
                p.octavecheck = p.octave
            p.makeRelative(last)
            if relPitch:
                # we are allowed to change the pitch after the
                # \relative command. lastPitch contains this pitch.
                lastPitch.octave += p.octave
                p.octave = 0
                pitches.write(lastPitch)
                del relPitch[:]
            pitches.write(p)
            return newLastPitch

        lastPitch = None
        relPitch = [] # we use a list so it can be changed from inside functions
        
        # find the pitch after the \relative command
        t = next(tsource)
        if isinstance(t, ly.pitch.Pitch):
            lastPitch = t
            if in_selection(t):
                relPitch.append(lastPitch)
            t = next(tsource)
        elif relative_first_pitch_absolute:
            lastPitch = ly.pitch.Pitch.f0()
        else:
            lastPitch = ly.pitch.Pitch.c1()
        
        while True:
            # eat stuff like \new Staff == "bla" \new Voice \notes etc.
            if isinstance(source.state.parser(), ly.lex.lilypond.ParseTranslator):
                t = consume()
            elif isinstance(t, ly.lex.lilypond.NoteMode):
                t = next(tsource)
            else:
                break
        
        # now transpose the relative expression
        if t in ('{', '<<'):
            # Handle full music expression { ... } or << ... >>
            for t in context():
                if t == '\\octaveCheck':
                    for p in getpitches(context()):
                        lastPitch = p.copy()
                        del relPitch[:]
                        if in_selection(p):
                            transposer.transpose(p)
                            lastPitch.transposed = p
                            pitches.write(p)
                elif isinstance(t, ly.lex.lilypond.ChordStart):
                    chord = [lastPitch]
                    for p in getpitches(context()):
                        chord.append(transposeRelative(p, chord[-1]))
                    lastPitch = chord[:2][-1] # same or first
                elif isinstance(t, ly.pitch.Pitch):
                    lastPitch = transposeRelative(t, lastPitch)
        elif isinstance(t, ly.lex.lilypond.ChordStart):
            # Handle just one chord
            for p in getpitches(context()):
                lastPitch = transposeRelative(p, lastPitch)
        elif isinstance(t, ly.pitch.Pitch):
            # Handle just one pitch
            transposeRelative(t, lastPitch)

    # Do it!
    with cursor.document as document:
        absolute(tsource)

