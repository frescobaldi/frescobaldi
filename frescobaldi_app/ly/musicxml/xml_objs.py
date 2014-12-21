# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
Classes that holds information suitable for converting to musicXML.
"""

from __future__ import unicode_literals
from __future__ import print_function

from fractions import Fraction

class Score():
    """Object that keep track of a whole score."""
    def __init__(self):
        self.partlist = []
        self.title = None
        self.creators = {}
        self.info = {}
        self.rights = None

    def is_empty(self):
        """Check if score is empty."""
        if self.partlist:
            return False
        else:
            return True

    def debug_score(self, attr=[]):
        """
        Loop through score and print all elements for debugging purposes.

        Additionally print element attributes by adding them to the
        argument 'attr' list.

        """
        ind = "  "
        def debug_part(p):
            print("Score part:"+p.name)
            for n, b in enumerate(p.barlist):
                print(ind+"Bar nr: "+str(n+1))
                for obj in b.obj_list:
                    print(ind+ind+repr(obj))
                    for a in attr:
                        try:
                            print(ind+ind+ind+a+':'+repr(getattr(obj, a)))
                        except AttributeError:
                            pass

        def debug_group(g):
            if hasattr(g, 'barlist'):
                debug_part(g)
            else:
                print("Score group:"+g.name)
                for pg in g.partlist:
                    debug_group(pg)

        for i in self.partlist:
            debug_group(i)


class ScorePartGroup():
    """Object to keep track of part group."""
    def __init__(self, num, bracket):
        self.bracket = bracket
        self.partlist = []
        self.name = ''
        self.abbr = ''
        self.parent = None
        self.num = num

    def set_bracket(self, bracket):
        self.bracket = bracket


class ScorePart():
    """ object to keep track of part """
    def __init__(self, staves=0):
        self.name = ''
        self.abbr = ''
        self.midi = ''
        self.barlist = []
        self.staves = staves

    def set_first_bar(self, divisions):
        initime = [4,4]
        iniclef = ('G',2,0)

        def check_time(bar):
            for obj in bar.obj_list:
                if isinstance(obj, BarAttr):
                    if obj.time:
                        return True
                if isinstance(obj, BarMus):
                    return False

        def check_clef(bar):
            for obj in bar.obj_list:
                if isinstance(obj, BarAttr):
                    if obj.clef or obj.multiclef:
                        return True
                if isinstance(obj, BarMus):
                    return False

        if not check_time(self.barlist[0]):
            try:
                self.barlist[0].obj_list[0].set_time(initime, False)
            except AttributeError:
                print("Warning can't set initial time sign!")
        if not check_clef(self.barlist[0]):
            try:
                self.barlist[0].obj_list[0].set_clef(iniclef)
            except AttributeError:
                print("Warning can't set initial clef sign!")
        self.barlist[0].obj_list[0].divs = divisions
        if self.staves:
            self.barlist[0].obj_list[0].staves = self.staves


class ScoreSection():
    """ object to keep track of music section """
    def __init__(self, name):
        self.name = name
        self.barlist = []

    def merge_voice(self, voice):
        for org_v, add_v in zip(self.barlist, voice.barlist):
            org_v.inject_voice(add_v)

    def merge_lyrics(self, lyrics):
        """Merge in lyrics in music section."""
        i = 0
        ext = False
        for bar in self.barlist:
            for obj in bar.obj_list:
                if isinstance(obj, BarNote):
                    if ext:
                        if obj.slur:
                            ext = False
                    else:
                        try:
                            l = lyrics.barlist[i]
                        except IndexError:
                            break
                        if l != 'skip':
                            try:
                                if l[3] == "extend" and obj.slur:
                                    ext = True
                            except IndexError:
                                pass
                            obj.add_lyric(l)
                        i += 1


class Snippet(ScoreSection):
    """ Short section indended to be merged.
    Holds reference to the barlist to be merged into."""
    def __init__(self, name, merge_into):
        ScoreSection.__init__(self, name)
        self.merge_barlist = merge_into


class LyricsSection(ScoreSection):
    """ Holds the lyrics information. Will eventually be merged to
    the corresponding note in the section set by the voice id. """
    def __init__(self, name, voice_id):
        ScoreSection.__init__(self, name)
        self.voice_id = voice_id


class Bar():
    """ Representing the bar/measure.
    Contains also information about how complete it is."""
    def __init__(self):
        self.obj_list = []
        self.list_full = False

    def add(self, obj):
        self.obj_list.append(obj)

    def has_music(self):
        """ Check if bar contains music. """
        for obj in self.obj_list:
            if isinstance(obj, BarMus):
                return True
        return False

    def create_backup(self):
        """ Calculate and create backup object."""
        b = 0
        s = 1
        for obj in self.obj_list:
            if isinstance(obj, BarMus):
                if not obj.chord:
                    b += obj.duration[0]
                    s *= obj.duration[1]
            elif isinstance(obj, BarBackup):
                break
        self.add(BarBackup((b,s)))

    def is_skip(self):
        """ Check if bar has nothing but skips. """
        for obj in self.obj_list:
            if obj.has_attr():
                return False
            if isinstance(obj, BarNote):
                return False
            elif isinstance(obj, BarRest):
                if not obj.skip:
                    return False
        return True

    def inject_voice(self, new_voice):
        """ Adding new voice to bar.
        Omitting double or conflicting bar attributes.
        Omitting also bars with only skips."""
        if new_voice.obj_list[0].has_attr():
            if not self.obj_list[0].has_attr():
                self.obj_list.insert(0, new_voice.obj_list[0])
            if new_voice.obj_list[0].multiclef:
                self.obj_list[0].multiclef += new_voice.obj_list[0].multiclef
            new_voice.obj_list.pop(0)
        try:
            if self.obj_list[-1].barline and new_voice.obj_list[-1].barline:
               self.obj_list.pop()
        except AttributeError:
            pass
        if not new_voice.is_skip():
            self.create_backup()
            for nv in new_voice.obj_list:
                self.add(nv)


class BarMus():
    """ Common class for notes and rests. """
    def __init__(self, duration, voice=1):
        self.duration = duration
        self.type = None
        self.tuplet = 0
        self.dot = 0
        self.voice = voice
        self.staff = 0
        self.chord = False
        self.other_notation = None
        self.dynamic = {
        'before': {'mark': None, 'wedge': None },
        'after': {'mark': None, 'wedge': None }
        }
        self.oct_shift = None

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.duration)

    def set_tuplet(self, fraction, ttype):
        self.tuplet = fraction
        self.ttype = ttype

    def set_staff(self, staff):
        self.staff = staff

    def add_dot(self):
        self.dot += 1

    def add_other_notation(self, other):
        self.other_notation = other

    def set_dynamics_before(self, mark=None, wedge=None):
        if mark:
            self.dynamic['before']['mark'] = mark
        if wedge:
            self.dynamic['before']['wedge'] = wedge

    def set_dynamics_after(self, mark=None, wedge=None):
        if mark:
            self.dynamic['after']['mark'] = mark
        if wedge:
            self.dynamic['after']['wedge'] = wedge

    def set_oct_shift(self, plac, octdir, size):
        self.oct_shift = OctaveShift(plac, octdir, size)

    def has_attr(self):
        return False


##
# Classes that are used by BarMus
##


class OctaveShift():
    """Class for octave shifts."""
    def __init__(self, plac, octdir, size):
        self.plac = plac
        self.octdir = octdir
        self.size = size


##
# Subclasses of BarMus
##


class BarNote(BarMus):
    """ object to keep track of note parameters """
    def __init__(self, pitch_note, alter, accidental, duration, voice=1):
        BarMus.__init__(self, duration, voice)
        self.base_note = pitch_note
        self.alter = alter
        self.octave = None
        self.accidental_token = accidental
        self.tie = []
        self.grace = (0,0)
        self.gliss = None
        self.tremolo = ('',0)
        self.skip = False
        self.slur = []
        self.artic = []
        self.ornament = None
        self.adv_ornament = None
        self.fingering = None
        self.lyric = None

    def set_duration(self, duration, durval=0):
        self.duration = duration
        self.dot = 0
        if durval:
            self.type = durval2type(durval)

    def set_durtype(self, durval):
        self.type = durval2type(durval)

    def set_octave(self, octave):
        self.octave = octave

    def set_tie(self, tie_type):
        self.tie.append(tie_type);

    def set_slur(self, slur_type):
        self.slur.append(slur_type)

    def add_articulation(self, art_name):
        self.artic.append(art_name)

    def add_ornament(self, ornament):
        self.ornament = ornament

    def add_adv_ornament(self, ornament, end_type="start"):
        self.adv_ornament = (ornament, {"type": end_type})

    def set_grace(self, slash):
        self.grace = (1,slash)

    def set_gliss(self, line, endtype = "start", nr=1):
        if not line:
            line = "solid"
        self.gliss = (line, endtype, nr)

    def set_tremolo(self, trem_type, duration=False):
        if duration:
            self.tremolo = (trem_type, dur2lines(duration))
        else:
            self.tremolo = (trem_type, self.tremolo[1])

    def add_fingering(self, finger_nr):
        self.fingering = finger_nr

    def add_lyric(self, lyric_list):
        if not self.lyric:
            self.lyric = []
        self.lyric.append(lyric_list)

    def change_lyric_syll(self, index, syll):
        self.lyric[index][1] = syll

    def change_lyric_nr(self, index, nr):
        self.lyric[index][2] = nr


class BarRest(BarMus):
    """ object to keep track of different rests and skips """
    def __init__(self, duration, voice=1, show_type=True, skip=False, pos=0):
        BarMus.__init__(self, duration, voice)
        self.show_type = show_type
        self.type = None
        self.skip = skip
        self.pos = pos

    def set_duration(self, duration, durval=0, durtype=None):
        self.duration = duration
        if durval:
            if self.show_type:
                self.type = durval2type(durval)
            else:
                self.type = None

    def set_durtype(self, durval):
        if self.show_type:
            self.type = durval2type(durval)


class BarAttr():
    """ object that keep track of bar attributes, e.g. time sign, clef, key etc """
    def __init__(self):
        self.key = None
        self.time = 0
        self.clef = 0
        self.mode = ''
        self.divs = 0
        self.barline = None
        self.repeat = None
        self.staves = 0
        self.multiclef = []
        self.tempo = None

    def __repr__(self):
        return '<{0}>'.format(self.__class__.__name__)

    def set_key(self, muskey, mode):
        self.key = muskey
        self.mode = mode

    def set_time(self, fractlist, numeric):
        self.time = fractlist
        if not numeric and (fractlist == [2,2] or fractlist == [4,4]):
            self.time.append('common')

    def set_clef(self, clef):
        self.clef = clef

    def set_barline(self, bl):
        self.barline = convert_barl(bl)

    def set_tempo(self, unit, beats, dots=0, text=""):
        self.tempo = TempoDir(unit, beats, dots, text)

    def has_attr(self):
        check = False
        if self.key is not None:
            check = True
        elif self.time != 0:
            check = True
        elif self.clef != 0:
            check = True
        elif self.multiclef:
            check = True
        elif self.divs != 0:
            check = True
        return check


class BarBackup():
    """ Object that stores duration for backup """
    def __init__(self, duration):
        self.duration = duration


class TempoDir():
    """ Object that stores tempo direction information """
    def __init__(self, unit, beats, dots, text):
        self.metr = durval2type(unit), beats
        self.text = text
        self.midi = self.set_midi_tempo(unit, beats, dots)
        self.dots = dots

    def set_midi_tempo(self, unit, beats, dots):
        u = Fraction(1,int(unit))
        if dots:
            import math
            den = int(math.pow(2,dots))
            num = int(math.pow(2,dots+1)-1)
            u *= Fraction(num, den)
        mult = 4*u
        return float(Fraction(beats)*mult)


##
# Translation functions
##

def durval2type(durval):
    import ly.duration
    xml_types = [
        "maxima", "long", "breve", "whole",
        "half", "quarter", "eighth",
        "16th", "32nd", "64th",
        "128th", "256th", "512th", "1024th", "2048th"
    ] # Note: 2048 is supported by ly but not by MusicXML!
    return xml_types[ly.duration.durations.index(durval)]

def dur2lines(dur):
    if dur == 8:
        return 1
    elif dur == 16:
        return 2
    elif dur == 32:
        return 3
    else:
        return 0

def convert_barl(bl):
    if bl == '|':
        return 'regular'
    elif bl == ':':
        return 'dotted'
    elif bl == 'dashed':
        return bl
    elif bl == '.':
        return 'heavy'
    elif bl == '||':
        return 'light-light'
    elif bl == '.|' or bl == 'forward':
        return 'heavy-light'
    elif bl == '.|.':
        return 'heavy-heavy'
    elif bl == '|.' or bl == 'backward':
        return 'light-heavy'
    elif bl == "'":
        return 'tick'

