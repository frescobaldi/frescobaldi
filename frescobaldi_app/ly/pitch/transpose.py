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
Transposing music.
"""

from __future__ import unicode_literals

from fractions import Fraction


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


