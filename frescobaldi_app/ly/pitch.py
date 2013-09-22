# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Pitch manipulation.
"""

from __future__ import unicode_literals

import re
from fractions import Fraction
import math


pitchInfo = {
    'nederlands': (
        ('c','d','e','f','g','a','b'),
        ('eses', 'eseh', 'es', 'eh', '', 'ih','is','isih','isis'),
        (('ees', 'es'), ('aes', 'as'))
    ),
    'english': (
        ('c','d','e','f','g','a','b'),
        ('ff', 'tqf', 'f', 'qf', '', 'qs', 's', 'tqs', 'ss'),
    ),
    'deutsch': (
        ('c','d','e','f','g','a','h'),
        ('eses', 'eseh', 'es', 'eh', '', 'ih','is','isih','isis'),
        (('ees', 'es'), ('aes', 'as'), ('hes', 'b'))
    ),
    'svenska': (
        ('c','d','e','f','g','a','h'),
        ('essess', '', 'ess', '', '', '','iss','','ississ'),
        (('ees', 'es'), ('aes', 'as'), ('hess', 'b'))
    ),
    'italiano': (
        ('do', 're', 'mi', 'fa', 'sol', 'la', 'si'),
        ('bb', 'bsb', 'b', 'sb', '', 'sd', 'd', 'dsd', 'dd')
    ),
    'espanol': (
        ('do', 're', 'mi', 'fa', 'sol', 'la', 'si'),
        ('bb', '', 'b', '', '', '', 's', '', 'ss')
    ),
    'portugues': (
        ('do', 're', 'mi', 'fa', 'sol', 'la', 'si'),
        ('bb', 'btqt', 'b', 'bqt', '', 'sqt', 's', 'stqt', 'ss')
    ),
    'vlaams': (
        ('do', 're', 'mi', 'fa', 'sol', 'la', 'si'),
        ('bb', '', 'b', '', '', '', 'k', '', 'kk')
    ),
}
pitchInfo['norsk'] = pitchInfo['deutsch']
pitchInfo['suomi'] = pitchInfo['deutsch']
pitchInfo['catalan'] = pitchInfo['italiano']


class PitchNameNotAvailable(Exception):
    """Exception raised when there is no name for a pitch.
    
    Can occur when translating pitch names, if the target language e.g.
    does not have quarter-tone names.
    
    """
    pass


class Pitch(object):
    """A pitch with note, alter and octave attributes.
    
    Attributes may be manipulated directly.
    
    """
    def __init__(self, note=0, alter=0, octave=0):
        self.note = note        # base note (c, d, e, f, g, a, b)
                                # as integer (0 to 6)
        self.alter = alter      # # = .5; b = -.5; natural = 0
        self.octave = octave    # '' = 2; ,, = -2
    
    def __repr__(self):
        return '<Pitch {0}>'.format(self.output())
    
    def output(self, language="nederlands"):
        """Returns our string representation."""
        return (
            pitchWriter(language)(self.note, self.alter) +
            octaveToString(self.octave))
        
    @classmethod
    def c1(cls):
        """Returns a pitch c'."""
        return cls(octave=1)

    @classmethod
    def c0(cls):
        """Returns a pitch c."""
        return cls()

    def copy(self):
        """Returns a new instance with our attributes."""
        return self.__class__(self.note, self.alter, self.octave)
        
    def makeAbsolute(self, lastPitch):
        """Makes ourselves absolute, i.e. sets our octave from lastPitch."""
        self.octave += lastPitch.octave - (self.note - lastPitch.note + 3) // 7
        
    def makeRelative(self, lastPitch):
        """Makes ourselves relative, i.e. changes our octave from lastPitch."""
        self.octave -= lastPitch.octave - (self.note - lastPitch.note + 3) // 7


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
        circleOfFifths = ['Cb','Gb','Db','Ab','Eb','Bb','F','C','G','D','A','E','B','F#','C#']
        return circleOfFifths.index(text.capitalize())
                  
    def transpose(self, pitch):
        # Look for an exact match: otherwise,
        # look for the letter name and save the accidental
        for i in range(len(self.notes)):
            if pitch.note == self.notes[i] and \
               pitch.alter == self.alter:
                    fromScaleDeg = i
                    accidental = 0
                    break;
        else:
            fromScaleDeg = self.notes.index(pitch.note)
            accidental = pitch.alter - self.alter[fromScaleDeg]
        
        toOctaveMod, toScaleDeg = divmod(fromScaleDeg + self.numSteps, 7)
        pitch.note = self.notes[toScaleDeg]
        pitch.alter = self.alter[toScaleDeg] + accidental
        pitch.octave += toOctaveMod


class PitchWriter(object):
    def __init__(self, names, accs, replacements=()):
        self.names = names
        self.accs = accs
        self.replacements = replacements

    def __call__(self, note, alter = 0):
        """
        Returns a string representing the pitch in our language.
        Raises PitchNameNotAvailable if the requested pitch
        has an alteration that is not available in the current language.
        """
        pitch = self.names[note]
        if alter:
            acc = self.accs[int(alter * 4 + 4)]
            if not acc:
                raise PitchNameNotAvailable()
            pitch += acc
        for s, r in self.replacements:
            if pitch.startswith(s):
                pitch = r + pitch[len(s):]
                break
        return pitch


class PitchReader(object):
    def __init__(self, names, accs, replacements=()):
        self.names = list(names)
        self.accs = list(accs)
        self.replacements = replacements
        self.rx = re.compile("({0})({1})?$".format("|".join(names),
            "|".join(acc for acc in accs if acc)))

    def __call__(self, text):
        for s, r in self.replacements:
            if text.startswith(r):
                text = s + text[len(r):]
        for dummy in 1, 2:
            m = self.rx.match(text)
            if m:
                note = self.names.index(m.group(1))
                if m.group(2):
                    alter = Fraction(self.accs.index(m.group(2)) - 4, 4)
                else:
                    alter = 0
                return note, alter
            # HACK: were we using (rarely used) long english syntax?
            text = text.replace('flat', 'f').replace('sharp', 's')
        return False
            
            
def octaveToString(octave):
    """Converts numeric octave to a string with apostrophes or commas.
    
    0 -> "" ; 1 -> "'" ; -1 -> "," ; etc.
    
    """
    return octave < 0 and ',' * -octave or "'" * octave


def octaveToNum(octave):
    """Converts string octave to an integer:
    
    "" -> 0 ; "," -> -1 ; "'''" -> 3 ; etc.
    
    """
    return octave.count("'") - octave.count(",")


_pitchReaders = {}
_pitchWriters = {}


def pitchReader(language):
    """Returns a PitchReader for the speficied language."""
    try:
        return _pitchReaders[language]
    except KeyError:
        res = _pitchReaders[language] = PitchReader(*pitchInfo[language])
        return res


def pitchWriter(language):
    """Returns a PitchWriter for the speficied language."""
    try:
        return _pitchWriters[language]
    except KeyError:
        res = _pitchWriters[language] = PitchWriter(*pitchInfo[language])
        return res


