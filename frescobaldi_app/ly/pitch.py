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

from __future__ import unicode_literals

import re
from fractions import Fraction


class QuarterToneNotAvailable(Exception):
    """
    Raised when there is no pitch name in the target languate
    when translating pitch names.
    """
    pass


class Pitch(object):
    """
    A pitch with note, alter, octave and cautionary and octaveCheck
    (for relative pitches)
    """
    def __init__(self):
        self.note = 0           # base note (c, d, e, f, g, a, b)
        self.alter = 0          # # = 2; b = -2; natural = 0
        self.octave = 0         # '' = 2; ,, = -2
        self.cautionary = ''    # '!' or '?' or ''
        self.octaveCheck = None
    
    @classmethod
    def c1(cls):
        """ Return a pitch c' """
        p = cls()
        p.octave = 1
        return p

    @classmethod
    def c0(cls):
        """ Return a pitch c """
        return cls()

    def copy(self):
        """ Return a new instance with our attributes. """
        p = self.__class__()
        p.note = self.note
        p.alter = self.alter
        p.octave = self.octave
        p.cautionary = self.cautionary
        p.octaveCheck = self.octaveCheck
        return p
        
    def absolute(self, lastPitch):
        """
        Set our octave height from lastPitch (which is absolute), as if
        we are a relative pitch. If the octaveCheck attribute is set to an
        octave number, that is used instead.
        """
        if self.octaveCheck is not None:
            self.octave = self.octaveCheck
            self.octaveCheck = None
        else:
            dist = self.note - lastPitch.note
            if dist > 3:
                dist -= 7
            elif dist < -3:
                dist += 7
            self.octave += lastPitch.octave  + (lastPitch.note + dist) // 7
        
    def relative(self, lastPitch):
        """
        Returns a new Pitch instance with the current pitch relative to
        the absolute pitch in lastPitch.
        """
        p = self.copy()
        dist = self.note - lastPitch.note
        p.octave = self.octave - lastPitch.octave + (dist + 3) // 7
        return p
        
    def output(self, language):
        """
        Return the pitch as a string in the given pitch name language.
        Raises QuarterToneNotAvailable is an alteration is
        requested that is not available in that language.
        """
        output = [pitchWriter[language](self.note, self.alter),
                  octaveToString(self.octave),
                  self.cautionary]
        if self.octaveCheck is not None:
            output.append('=' + octaveToString(self.octaveCheck))
        return ''.join(output)


class Transposer(object):
    """
    Transpose pitches.
    
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


class PitchWriter(object):
    def __init__(self, names, accs, replacements=()):
        self.names = names
        self.accs = accs
        self.replacements = replacements

    def __call__(self, note, alter = 0):
        """
        Returns a string representing the pitch in our language.
        Raises QuarterToneNotAvailable if the requested pitch
        has an alteration that is not available in the current language.
        """
        pitch = self.names[note]
        if alter:
            acc = self.accs[int(alter * 4 + 4)]
            if not acc:
                raise QuarterToneNotAvailable()
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
    """
    Convert numeric octave to a string with apostrophes or commas.
    0 -> "" ; 1 -> "'" ; -1 -> "," ; etc.
    """
    return octave < 0 and ',' * -octave or "'" * octave

def octaveToNum(octave):
    """
    Convert string octave to an integer:
    "" -> 0 ; "," -> -1 ; "'''" -> 3 ; etc.
    """
    return octave.count("'") - octave.count(",")


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


pitchWriter = dict(
    (lang, PitchWriter(*data)) for lang, data in pitchInfo.iteritems())

pitchReader = dict(
    (lang, PitchReader(*data)) for lang, data in pitchInfo.iteritems())


