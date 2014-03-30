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
Help class between the ly source parser and the XML creator
"""

from __future__ import unicode_literals

from fractions import Fraction

import ly.duration
import ly.pitch


class mediator():
    """ Help class between the ly source parser and the XML creator """

    def __init__(self):
        """ create global lists """
        self.score = []
        self.sections = []
        """ default and initial values """
        self.current_note = None
        self.divisions = 1
        self.duration = "4"
        self.base_scaling = [Fraction(1, 4), Fraction(1, 1)]
        self.dots = 0
        self.tied = False
        self.voice = 1
        self.current_chord = []
        self.new_chord = True

    def new_section(self, name):
        n = self.get_var_byname(name)
        if n:
            n.name = name+"-old"
        section = score_section(name)
        self.insert_into = section
        self.sections.append(section)
        self.bar = None

    def get_var_byname(self, name):
        for n in self.sections:
            if n.name == name:
                return n

    def new_part(self, piano=False):
        if piano:
            self.part = score_part(2)
        else:
            self.part = score_part()
        self.score.append(self.part)
        self.insert_into = self.part
        self.bar = None

    def new_voice(self, command):
        self.voice = get_voice(command)
        return self.voice

    def merge_variable(self, voice, varname, staff=False, org=None):
        """ Fetches variable as new voice """
        if org:
            merge_org = self.get_var_byname(org)
        else:
            merge_org = self.insert_into
        n = self.get_var_byname(varname)
        varlen = len(n.barlist)
        if staff:
            if isinstance(merge_org.barlist[0][0], bar_attr):
                clef_one = merge_org.barlist[0][0].clef
                if clef_one:
                    merge_org.barlist[0][0].multiclef.append(clef_one)
                else:
                    merge_org.barlist[0][0].multiclef.append(['G',2])
                if isinstance(n.barlist[0][0], bar_attr):
                    clef_two = n.barlist[0][0].clef
                    if clef_two:
                        merge_org.barlist[0][0].multiclef.append(clef_two)
                    else:
                        merge_org.barlist[0][0].multiclef.append(['G',2])
                    merge_org.barlist[0][0].clef = 0
            self.set_staff(merge_org.barlist, 1, False)
            self.set_staff(n.barlist, 2)
        if voice>4:
            self.change_voice(n.barlist, voice, plusvoice=True)
        elif voice:
            self.change_voice(n.barlist, voice)
        for i, bar in enumerate(merge_org.barlist):
            if i < varlen:
                if self.check_bar(n.barlist[i]):
                    backup = self.create_backup(bar)
                    merge_org.barlist[i] = bar + [backup] + n.barlist[i]

    def change_voice(self, barlist, newvoice, del_barattr=True, plusvoice=False):
        for bar in barlist:
            orig = list(bar)
            for obj in orig:
                if isinstance(obj, bar_note) or isinstance(obj, bar_rest):
                    if plusvoice:
                        obj.voice += 4
                    else:
                        obj.voice = newvoice
                elif isinstance(obj, bar_attr):
                    if del_barattr:
                        bar.remove(obj)

    def set_staff(self, barlist, staffnr, del_barattr=True):
        for bar in barlist:
            orig= list(bar)
            for obj in orig:
                if isinstance(obj, bar_note) or isinstance(obj, bar_rest):
                    obj.staff = staffnr
                elif isinstance(obj, bar_attr):
                    if del_barattr:
                        bar.remove(obj)

    def create_backup(self, bar):
        b = 0
        s = 1
        for obj in bar:
            if isinstance(obj, bar_note) or isinstance(obj, bar_rest):
                if not obj.chord:
                    if obj.dot:
                        import math
                        den = int(math.pow(2,obj.dot))
                        num = int(math.pow(2,obj.dot+1)-1)
                        b += Fraction(num, den)*obj.duration[0]
                    else:
                        b += obj.duration[0]
                    s *= obj.duration[1]
            elif isinstance(obj, bar_backup):
                self.check_divs(b, s)
                return bar_backup([b,s])
        if b:
            self.check_divs(b, s)
        return bar_backup((b,s))

    def fetch_variable(self, varname):
        """ Fetches stored data for variable. """
        n = self.get_var_byname(varname)
        if n.barlist:
            if self.check_var(n.barlist):
                if self.insert_into.barlist and not self.check_bar(self.insert_into.barlist[-1]):
                    n.barlist[0] = self.insert_into.barlist[-1] + n.barlist[0]
                    self.insert_into.barlist.pop()
                self.insert_into.barlist.extend(n.barlist)
            elif isinstance(n.barlist[0][0], bar_attr):
                if self.bar is None:
                    self.new_bar()
                self.current_attr = n.barlist[0][0]
                self.bar.append(self.current_attr)

    def check_var(self, barlist):
        """ Check if barlist in variable is suitable for insert.
        For now if variable contains notes full bars are assumed."""
        for bar in barlist:
            for obj in bar:
                if isinstance(obj, bar_note):
                    return True
        return False

    def check_bar(self, bar):
        """ For variable handling.
        Ideally the function should check if the bar is incomplete.
        For now it only checks if the bar contains music. """
        for obj in bar:
            if isinstance(obj, bar_note) or isinstance(obj, bar_rest):
                if not obj.skip:
                    return True
        return False

    def check_score(self):
        """ if no part were created, place first variable as part. """
        if not self.score:
            self.new_part()
            self.part.barlist.extend(self.get_first_var())

    def get_first_var(self):
        for n in self.sections:
            if self.check_var(n.barlist):
                return n.barlist

    def set_first_bar(self, part):
        initime = '4/4'
        iniclef = 'G',2,0
        if not self.check_time(part.barlist[0]):
            part.barlist[0][0].set_time(initime, False)
        if not self.check_clef(part.barlist[0]):
            part.barlist[0][0].set_clef(iniclef)
        part.barlist[0][0].divs = self.divisions
        if part.staves:
            part.barlist[0][0].staves = part.staves

    def check_time(self, bar):
        """ For now used to check first bar """
        for obj in bar:
            if isinstance(obj, bar_attr):
                if obj.time:
                    return True
            if isinstance(obj, bar_note):
                return False

    def check_clef(self, bar):
        """ For now used to check first bar """
        for obj in bar:
            if isinstance(obj, bar_attr):
                if obj.clef or obj.multiclef:
                    return True
            if isinstance(obj, bar_note):
                return False

    def new_bar(self):
        self.current_attr = bar_attr()
        self.bar = [self.current_attr]
        self.insert_into.barlist.append(self.bar)

    def create_barline(self, bl):
        barline = bar_attr()
        barline.set_barline(bl)
        self.bar.append(barline)
        self.new_bar()

    def new_repeat(self, rep):
        barline = bar_attr()
        barline.set_barline(rep)
        barline.repeat = rep
        if self.bar is None:
            self.new_bar()
        self.bar.append(barline)

    def new_key(self, key_name, mode_command):
        mode = mode_command[1:]
        if self.bar is None:
            self.new_bar()
        self.current_attr.set_key(get_fifths(key_name, mode), mode)

    def new_time(self, fraction, numeric=False):
        if self.bar is None:
            self.new_bar()
        self.current_attr.set_time(fraction, numeric)

    def new_clef(self, clefname):
        self.clef = clefname2clef(clefname)
        if self.bar is None:
            self.new_bar()
        self.current_attr.set_clef(self.clef)

    def set_relative(self, note_name):
        self.current_note = bar_note(note_name, self.base_scaling, self.duration, self.voice)
        self.set_prev_pitch()

    def set_prev_pitch(self):
        p = self.current_note.pitch
        self.prev_pitch = ly.pitch.Pitch(p.note, p.alter, p.octave)

    def new_note(self, note_name, pitch_mode):
        self.current_chord = []
        self.current_note = bar_note(note_name, self.base_scaling, self.duration, self.voice)
        if self.dots:
            self.current_note.dot = self.dots
        if pitch_mode == 'rel':
            self.current_note.set_octave("", True, self.prev_pitch)
        if self.tied:
            self.current_note.set_tie('stop')
            self.tied = False
        if self.bar is None:
            self.new_bar()
        self.bar.append(self.current_note)
        self.current_attr = bar_attr()
        self.set_prev_pitch()

    def create_chord(self, note_name, pitch_mode):
        if self.new_chord:
            self.new_note(note_name, pitch_mode)
            self.current_chord.append(self.current_note)
        else:
            self.current_chord.append(self.new_chordnote(note_name, pitch_mode, len(self.current_chord)))

    def new_chordnote(self, note_name, pitch_mode, chord_len):
        chord_note = bar_note(note_name, self.base_scaling, self.duration, self.voice)
        if self.dots:
            chord_note.dot = self.dots
        if pitch_mode == 'rel':
            chord_note.set_octave("", True, self.current_chord[chord_len-1].pitch)
        chord_note.chord = True
        self.bar.append(chord_note)
        return chord_note

    def new_rest(self, rtype, pos=0):
        self.current_chord = []
        if rtype == 'r':
            self.current_note = bar_rest(self.base_scaling, self.duration, pos, self.voice)
        elif rtype == 'R':
            self.current_note = bar_rest(self.base_scaling, self.duration, pos, self.voice, show_type=False)
        elif rtype == 's':
            self.current_note = bar_rest(self.base_scaling, self.duration, pos, self.voice, skip=True)
        if self.bar is None:
            self.new_bar()
        self.bar.append(self.current_note)
        self.current_attr = bar_attr()

    def note2rest(self):
        """ note used as rest position transformed to rest"""
        temp_note = self.current_note
        self.current_note = bar_rest(temp_note.duration, self.duration, [temp_note.base_note, temp_note.pitch.octave], self.voice)
        self.bar.pop()
        self.bar.append(self.current_note)

    def scale_rest(self, multp, new_bar=False):
        """ create multiple whole bar rests """
        import copy
        bar_copy = copy.deepcopy(self.bar)
        bar_copy[0] = bar_attr()
        for i in range(1, int(multp)):
            self.insert_into.barlist.append(bar_copy)
        if new_bar:
            self.new_bar()

    def new_duration(self, duration):
        base, scaling = ly.duration.base_scaling_string(duration)
        if self.current_chord:
            for c in self.current_chord:
                c.set_duration([base, scaling], duration)
        else:
            self.current_note.set_duration([base, scaling], duration)
        self.duration = duration
        self.base_scaling = [base, scaling]
        self.check_divs(base, scaling, self.current_note.tuplet)
        self.dots = 0

    def scale_duration(self, scale):
        base, scaling = ly.duration.base_scaling_string(self.duration+scale)
        self.current_note.set_duration([base, scaling])
        self.base_scaling = [base, scaling]
        self.check_divs(base, scaling, self.current_note.tuplet)

    def change_to_tuplet(self, fraction, ttype):
        tfraction = Fraction(fraction)
        tfraction = 1/tfraction # delete this row with new tuplet notation
        self.current_note.set_tuplet(tfraction, ttype)

    def new_dot(self):
        self.current_note.add_dot()
        self.dots = self.current_note.dot
        if self.current_chord:
            for c in range(1, len(self.current_chord)):
                self.current_chord[c].add_dot()
        import math
        num = int(math.pow(2,self.dots))
        den = int(math.pow(2,self.dots+1)-1)
        dots = ''
        for i in range(self.dots):
            dots += '.'
        base, scaling = ly.duration.base_scaling_string(self.duration+dots)
        self.check_divs(base, scaling, self.current_note.tuplet)

    def tie_to_next(self):
        if self.current_note.tie == 'stop': # only if previous was tied
            self.current_note.set_tie('continue')
        else:
            self.current_note.set_tie('start')
        self.tied = True

    def new_grace(self, slash):
        self.current_note.set_grace(slash)

    def new_tremolo(self, duration):
        self.current_note.set_tremolo(duration)

    def new_octave(self, octave, relative=False):
        chordlen = len(self.current_chord)
        if chordlen > 1:
            prevp = self.current_chord[chordlen - 2].pitch
            self.current_chord[-1].set_octave(octave, relative, prevp)
        else:
            self.current_note.set_octave(octave, relative, self.prev_pitch)
            self.set_prev_pitch()

    def new_from_command(self, command):
        #print (command)
        pass

    def set_partname(self, name):
        self.part.name = name

    def check_divs(self, base, scaling, tfraction=0):
        """ The new duration is checked against current divisions """
        divs = self.divisions
        if scaling != 1:
            tfraction = scaling
        if(not tfraction):
            a = 4
            if base:
                b = 1/base
            else:
                b = 1
                print "Warning problem checking duration!"
        else:
            num = tfraction.numerator
            den = tfraction.denominator
            a = 4*den
            b = (1/base)*num
        c = a*divs
        predur, mod = divmod(c,b)
        if mod > 0:
            mult = get_mult(a,b)
            self.divisions = divs*mult


class score_part():
    """ object to keep track of part """
    def __init__(self, staves=0):
        self.name = ''
        self.barlist = []
        self.staves = staves

class score_section():
    """ object to keep track of music section """
    def __init__(self, name):
        self.name = name
        self.barlist = []

class bar_note():
    """ object to keep track of note parameters """
    def __init__(self, note_name, base_scaling, durval, voice):
        plist = notename2step(note_name)
        self.base_note = plist[0]
        self.pitch = ly.pitch.Pitch(plist[2], plist[1], 3)
        self.duration = base_scaling
        self.type = durval2type(durval)
        self.tuplet = 0
        self.dot = 0
        self.tie = 0
        self.grace = [0,0]
        self.tremolo = 0
        self.voice = voice
        self.staff = 0
        self.chord = False
        self.skip = False

    def set_duration(self, base_scaling, durval=0):
        self.duration = base_scaling
        self.dot = 0
        if durval:
            self.type = durval2type(durval)

    def set_octave(self, octmark, relative, prev_pitch):
        self.pitch.octave = ly.pitch.octaveToNum(octmark)
        if relative:
            self.pitch.makeAbsolute(prev_pitch)
        else:
            self.pitch.octave += 3; #adjusting to scientific pitch notation

    def set_tuplet(self, fraction, ttype):
        self.tuplet = fraction
        self.ttype = ttype

    def set_tie(self, tie_type):
        self.tie = tie_type

    def add_dot(self):
        self.dot = self.dot + 1

    def set_grace(self, slash):
        self.grace = [1,slash]

    def set_tremolo(self, duration):
        self.tremolo = dur2lines(duration)

class bar_rest():
    """ object to keep track of different rests and skips """
    def __init__(self, base_scaling, durval, pos, voice, show_type=True, skip=False):
        self.duration = base_scaling
        self.show_type = show_type
        if self.show_type:
            self.type = durval2type(durval)
        else:
            self.type = None
        self.skip = skip
        self.tuplet = 0
        self.dot = 0
        self.pos = pos
        self.voice = voice
        self.staff = 0
        self.chord = False

    def set_duration(self, base_scaling, durval=0, durtype=None):
        self.duration = base_scaling
        if durval:
            if self.show_type:
                self.type = durval2type(durval)
            else:
                self.type = None

    def add_dot(self):
        self.dot = self.dot + 1


class bar_attr():
    """ object that keep track of bar attributes, e.g. time sign, clef, key etc """
    def __init__(self):
        self.key = -1
        self.time = 0
        self.clef = 0
        self.mode = ''
        self.divs = 0
        self.barline = ''
        self.repeat = None
        self.staves = 0
        self.multiclef = []

    def set_key(self, muskey, mode):
        self.key = muskey
        self.mode = mode

    def set_time(self, fraction, numeric):
        mustime = fraction.split('/')
        if not numeric and (fraction == '2/2' or fraction == '4/4'):
            mustime.append('common')
        self.time = mustime

    def set_clef(self, clef):
        self.clef = clef

    def set_barline(self, bl):
        self.barline = convert_barl(bl)

    def has_attr(self):
        check = False
        if self.key != -1:
            check = True
        elif self.time != 0:
            check = True
        elif self.clef != 0:
            check = True
        elif self.divs != 0:
            check = True
        return check


class bar_backup():
    """ Object that stores duration for backup """
    def __init__(self, duration):
        self.duration = duration


##
# translation functions
##

def get_fifths(key, mode):
    sharpkeys = ['c', 'g', 'd', 'a', 'e', 'b', 'fis', 'cis', 'gis', 'dis', 'ais']
    flatkeys = ['c', 'f', 'bes', 'es', 'as', 'des', 'ges']
    if key in sharpkeys:
        fifths = sharpkeys.index(key)
    elif key in flatkeys:
        fifths = -flatkeys.index(key)
    if mode=='minor':
        return fifths-3
    elif mode=='major':
        return fifths

def clefname2clef(clefname):
    if clefname == "treble":
        return 'G',2,0
    elif clefname == "bass":
        return 'F',4,0
    elif clefname == "alto":
        return 'C',3,0
    elif clefname == "tenor":
        return 'C',4,0
    elif clefname == "treble_8":
        return 'G',2,-1
    elif clefname == "bass_8":
        return 'F',4,-1
    elif clefname == "treble^8":
        return 'G',2,1
    elif clefname == "bass^8":
        return 'F',4,1

def notename2step(note_name):
    alter = 0
    if len(note_name)>1:
        is_sharp = note_name.split('i')
        is_flat = note_name.split('e')
        note_name = note_name[0]
        if len(is_sharp)>1:
            alter = len(is_sharp)-1
        elif len(is_flat)>1:
            alter = -(len(is_flat)-1)
        else:
            alter = -1 #assuming 'as'
    base_list = ['c', 'd', 'e', 'f', 'g', 'a', 'b']
    note_num = base_list.index(note_name)
    return [note_name.upper(), alter, note_num]

def durval2type(durval):
    xml_types = [
        "maxima", "long", "breve", "whole",
        "half", "quarter", "eighth",
        "16th", "32nd", "64th",
        "128th", "256th", "512th", "1024th", "2048th"
    ] # Note: 2048 is supported by ly but not by MusicXML!
    return xml_types[ly.duration.durations.index(durval)]

def dur2lines(dur):
    if dur == "8":
        return 1
    if dur == "16":
        return 2
    if dur == "32":
        return 3

def get_mult(num, den):
    from fractions import Fraction
    simple = Fraction(num, den)
    return simple.denominator

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

def get_voice(c):
    voices = ["voiceOne", "voiceTwo", "voiceThree", "voiceFour"]
    return voices.index(c)+1




