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
The information of the parsed source is organised into an object
structure suitable for the transformation into a XML tree.
"""

from __future__ import unicode_literals

from fractions import Fraction

import ly.duration
import ly.pitch


class Mediator():
    """ Help class between the ly source parser and the XML creator """

    def __init__(self):
        """ create global lists """
        self.score = []
        self.sections = []
        """ default and initial values """
        self.current_note = None
        self.divisions = 1
        self.dur_token = "4"
        self.base_scaling = [Fraction(1, 4), Fraction(1, 1)]
        self.dots = 0
        self.tied = False
        self.voice = 1
        self.staff = 0
        self.current_chord = []
        self.prev_pitch = None
        self.store_voicenr = 0
        self.staff_id_dict = {}
        self.store_unset_staff = False
        self.staff_unset_notes = {}
        self.lyric_sections = {}

    def new_section(self, name):
        name = self.check_name(name)
        section = ScoreSection(name)
        self.insert_into = section
        self.sections.append(section)
        self.bar = None

    def new_snippet(self, name):
        name = self.check_name(name)
        snippet = Snippet(name, self.insert_into)
        self.insert_into = snippet
        self.sections.append(snippet)
        self.bar = None

    def new_lyric_section(self, name, voice_id):
        name = self.check_name(name)
        lyrics = LyricsSection(name, voice_id)
        self.insert_into = lyrics
        self.lyric_sections[name] = lyrics

    def check_name(self, name, nr=1):
        n = self.get_var_byname(name)
        if n:
            name = name+str(nr)
            name = self.check_name(name, nr+1)
        return name

    def get_var_byname(self, name):
        for n in self.sections:
            if n.name == name:
                return n

    def new_part(self, piano=False):
        if piano:
            self.part = ScorePart(2)
        else:
            self.part = ScorePart()
        self.score.append(self.part)
        self.insert_into = self.part
        self.bar = None

    def set_voicenr(self, command=None, add=False, nr=0, piano=0):
        if add:
            if not self.store_voicenr:
                self.store_voicenr = self.voice
            self.voice += 1
        elif nr:
            self.voice = nr
        else:
            self.voice = get_voice(command)
            if piano>2:
                self.voice += piano+1

    def revert_voicenr(self):
        self.voice = self.store_voicenr
        self.store_voicenr = 0

    def set_staffnr(self, staffnr, staff_id=None):
        self.store_unset_staff = False
        if staffnr:
            self.staff = staffnr
        elif staff_id in self.staff_id_dict:
            self.staff = self.staff_id_dict[staff_id]
        elif staff_id:
            self.store_unset_staff = True
            self.staff = staff_id

    def add_staff_id(self, staff_id):
        self.store_unset_staff = False
        if staff_id:
            self.staff_id_dict[staff_id] = self.staff
            if staff_id in self.staff_unset_notes:
                for n in self.staff_unset_notes[staff_id]:
                    n.staff = self.staff

    def add_snippet(self, snippet_name):
        """ Adds snippet to previous barlist.
        A snippet can be shorter than a full bar,
        so this can also mean continuing a previous bar."""
        def continue_barlist(insert_into):
            self.insert_into = insert_into
            if insert_into.barlist:
                self.bar = insert_into.barlist[-1]
            else:
                self.new_bar(False)

        snippet = self.get_var_byname(snippet_name)
        continue_barlist(snippet.merge_barlist)
        for bb in snippet.barlist:
            for b in bb.obj_list:
                self.bar.add(b)
            if bb.list_full:
                self.new_bar()

    def check_voices(self):
        """ Checks active sections. The two latest created are merged.
        Also checks for empty sections. """
        if len(self.sections)>2:
            if not self.sections[-2].barlist:
                self.sections.pop(-2)
                self.check_voices()
            elif not self.sections[-1].barlist:
                self.sections.pop()
                self.check_voices()
            else:
                self.sections[-2].merge_voice(self.sections[-1])
                self.sections.pop()

    def check_voices_by_nr(self):
        """ Used for snippets. Merges all active snippets
        created after the stored voice number."""
        sect_len = len(self.sections)
        if sect_len>2:
            if self.voice>1:
                for n in range(self.store_voicenr, self.voice):
                    self.check_voices()
                if isinstance(self.sections[-1], Snippet):
                    self.add_snippet(self.sections[-1].name)
                    self.sections.pop()
                else:
                    print("WARNING: problem adding snippet!")

    def check_lyrics(self, voice_id):
        """Check the finished lyrics section and merge it into
        the referenced voice."""
        lyrics_section = self.lyric_sections['lyricsto'+voice_id]
        voice_section = self.get_var_byname(lyrics_section.voice_id)
        if voice_section:
            voice_section.merge_lyrics(lyrics_section)

    def check_part(self):
        """Adds the latest active section to the part."""
        if len(self.sections)>1:
            if not self.score:
                self.new_part()
            self.part.barlist.extend(self.sections[-1].barlist)
            self.sections.pop()

    def check_score(self):
        """ If no part were created, place first variable (fallback) as part. """
        if not self.score:
            self.new_part()
            self.part.barlist.extend(self.get_first_var())

    def get_first_var(self):
        if self.sections:
            return self.sections[0].barlist

    def set_first_bar(self, part):
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

        if not check_time(part.barlist[0]):
            try:
                part.barlist[0].obj_list[0].set_time(initime, False)
            except AttributeError:
                print "Warning can't set initial time sign!"
        if not check_clef(part.barlist[0]):
            try:
                part.barlist[0].obj_list[0].set_clef(iniclef)
            except AttributeError:
                print "Warning can't set initial clef sign!"
        part.barlist[0].obj_list[0].divs = self.divisions
        if part.staves:
            part.barlist[0].obj_list[0].staves = part.staves

    def new_bar(self, fill_prev=True):
        if self.bar and fill_prev:
            self.bar.list_full = True
        self.current_attr = BarAttr()
        self.bar = Bar()
        self.bar.obj_list = [self.current_attr]
        self.insert_into.barlist.append(self.bar)

    def add_to_bar(self, obj):
        if self.bar is None:
            self.new_bar()
        self.bar.add(obj)

    def create_barline(self, bl):
        barline = BarAttr()
        barline.set_barline(bl)
        self.bar.add(barline)
        self.new_bar()

    def new_repeat(self, rep):
        barline = BarAttr()
        barline.set_barline(rep)
        barline.repeat = rep
        if self.bar is None:
            self.new_bar()
        self.bar.add(barline)

    def new_key(self, key_name, mode):
        if self.bar is None:
            self.new_bar()
        if self.bar.has_music():
            new_bar_attr = BarAttr()
            new_bar_attr.set_key(get_fifths(key_name, mode), mode)
            self.add_to_bar(new_bar_attr)
        else:
            self.current_attr.set_key(get_fifths(key_name, mode), mode)

    def new_time(self, num, den, numeric=False):
        if self.bar is None:
            self.new_bar()
        self.current_attr.set_time([num, den.denominator], numeric)

    def new_clef(self, clefname):
        self.clef = clefname2clef(clefname)
        if self.bar is None:
            self.new_bar()
        if self.bar.has_music():
            new_bar_attr = BarAttr()
            new_bar_attr.set_clef(self.clef)
            self.add_to_bar(new_bar_attr)
        else:
            if self.staff:
                self.current_attr.multiclef.append((self.clef, self.staff))
            else:
                self.current_attr.set_clef(self.clef)

    def set_relative(self, note):
        bar_note = BarNote(note)
        bar_note.set_octave(False)
        self.prev_pitch = bar_note.pitch

    def new_note(self, note, rel=False):
        self.clear_chord()
        self.current_note = BarNote(note, self.voice)
        self.check_current_note(rel)

    def check_current_note(self, rel=False, rest=False):
        """ Perform checks common for all new notes and rests. """
        if not rest: #don't do this for rests
            self.current_note.set_octave(rel, self.prev_pitch)
            if self.tied:
                self.current_note.set_tie('stop')
                self.tied = False
            self.prev_pitch = self.current_note.pitch
        self.check_duration(rest)
        self.check_divs()
        if self.staff:
            self.current_note.set_staff(self.staff)
            if self.store_unset_staff:
                if self.staff in self.staff_unset_notes:
                    self.staff_unset_notes[self.staff].append(self.current_note)
                else:
                    self.staff_unset_notes[self.staff] = [self.current_note]
        self.add_to_bar(self.current_note)

    def check_duration(self, rest):
        dur_tokens = self.current_note.duration.tokens
        dur_nr, dots, rs = self.duration_from_tokens(dur_tokens)
        if dur_nr:
            self.current_note.set_durtype(dur_nr)
            self.dur_token = dur_nr
            if rest and rs: # special case of multibar rest
                if not self.current_note.show_type or self.current_note.skip:
                    bs = self.current_note.base_scaling
                    if rs == bs[1]:
                        self.current_note.base_scaling = (bs[0], 1)
                        self.scale_rest(rs)
                        return
            self.current_note.dot = dots
            self.dots = dots
        else:
            self.current_note.set_durtype(self.dur_token)
            self.current_note.dot = self.dots

    def new_chord(self, note, duration, rel=False):
        if not self.current_chord:
            self.new_chordbase(note, duration, rel)
            self.current_chord.append(self.current_note)
        else:
            self.current_chord.append(self.new_chordnote(note, rel))

    def new_chordbase(self, note, duration, rel=False):
        self.current_note = BarNote(note, self.voice)
        self.current_note.set_duration(duration)
        self.check_current_note(rel)

    def new_chordnote(self, note, rel):
        chord_note = BarNote(note, self.voice)
        chord_note.set_duration(self.current_note.duration)
        chord_note.set_durtype(self.dur_token)
        chord_note.dots = self.dots
        chord_note.set_octave(rel, self.current_chord[-1].pitch)
        chord_note.chord = True
        self.bar.add(chord_note)
        return chord_note

    def copy_prev_chord(self, duration, rel):
        prev_chord = self.current_chord
        self.clear_chord()
        for pc in prev_chord:
            self.new_chord(pc.note, duration, rel)

    def clear_chord(self):
        self.current_chord = []

    def new_rest(self, rest):
        self.clear_chord()
        rtype = rest.token
        if rtype == 'r':
            self.current_note = BarRest(rest, self.voice)
        elif rtype == 'R':
            self.current_note = BarRest(rest, self.voice, show_type=False)
        elif rtype == 's' or rtype == '\skip':
            self.current_note = BarRest(rest, self.voice, skip=True)
        self.check_current_note(rest=True)

    def note2rest(self):
        """ note used as rest position transformed to rest"""
        temp_note = self.current_note
        self.current_note = BarRest(temp_note, temp_note.voice, pos = [temp_note.base_note, temp_note.pitch.octave])
        self.bar.obj_list.pop()
        self.bar.add(self.current_note)

    def scale_rest(self, multp):
        """ create multiple whole bar rests """
        cn = self.current_note
        st = self.current_note.show_type
        sk = self.current_note.skip
        for i in range(1, int(multp)):
            cn.note.duration.base_scaling = cn.base_scaling
            rest_copy = BarRest(cn.note, voice=cn.voice, show_type=st, skip=sk)
            self.add_to_bar(rest_copy)
            self.new_bar()

    def change_to_tuplet(self, fraction, ttype):
        tfraction = Fraction(fraction)
        tfraction = 1/tfraction
        self.current_note.set_tuplet(tfraction, ttype)
        self.check_divs(tfraction)

    def tie_to_next(self):
        if self.current_note.tie == 'stop': # only if previous was tied
            self.current_note.set_tie('continue')
        else:
            self.current_note.set_tie('start')
        self.tied = True

    def set_slur(self, slur_type):
        """
        Set the slur start or stop for the current note. """
        self.current_note.set_slur(slur_type)

    def new_articulation(self, art_token):
        """
        An articulation, fingering, string number, or other symbol.

        Grouped as articulations, ornaments, technical and others.
        """
        if isinstance(art_token, ly.lex.lilypond.Fingering):
            self.current_note.add_fingering(art_token)
        else:
            ret = artic_token2xml_name(art_token)
            if ret == 'ornament':
                self.current_note.add_ornament(art_token[1:])
            elif ret == 'other':
                self.current_note.add_other_notation(art_token[1:])
            elif ret:
                self.current_note.add_articulation(ret)

    def new_grace(self, slash=0):
        self.current_note.set_grace(slash)

    def set_tremolo(self, trem_type='single', duration=0, repeats=0):
        if self.current_note.tremolo[1]: #tremolo already set
            self.current_note.set_tremolo(trem_type)
        else:
            if not duration:
                duration = int(self.dur_token)
                bs, durtype = calc_trem_dur(repeats, self.current_note.base_scaling, duration)
                self.current_note.base_scaling = bs
                self.current_note.type = durtype
            self.current_note.set_tremolo(trem_type, duration)

    def new_tempo(self, dur_tokens, tempo, string):
        unit, dots = self.duration_from_tokens(dur_tokens)
        beats = tempo[0]
        text = string.value()
        tempo = BarAttr()
        tempo.set_tempo(unit, beats, dots, text)
        if self.bar is None:
            self.new_bar()
        self.bar.add(tempo)

    def set_partname(self, name):
        self.part.name = name

    def set_partmidi(self, midi):
        self.part.midi = midi

    def new_lyrics_text(self, txt):
        self.insert_into.barlist.append(txt)

    def new_lyrics_item(self, item):
        pass

    def duration_from_tokens(self, dur_tokens):
        dur_nr = 0
        dots = 0
        rs = 0
        for i, t in enumerate(dur_tokens):
            if i == 0:
                dur_nr = t
            elif t == '.':
                dots += 1
            elif '*' in t and '/' not in t:
                rs = int(t[1:])
        return (dur_nr, dots, rs)

    def check_divs(self, tfraction=0):
        """ The new duration is checked against current divisions """
        base = self.current_note.base_scaling[0]
        scaling = self.current_note.base_scaling[1]
        divs = self.divisions
        if scaling != 1:
            tfraction = 1/scaling
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

##
# Classes that holds information suitable for converting to XML.
##

class ScorePart():
    """ object to keep track of part """
    def __init__(self, staves=0):
        self.name = ''
        self.midi = ''
        self.barlist = []
        self.staves = staves


class ScoreSection():
    """ object to keep track of music section """
    def __init__(self, name):
        self.name = name
        self.barlist = []

    def merge_voice(self, voice):
        for org_v, add_v in zip(self.barlist, voice.barlist):
            org_v.inject_voice(add_v)

    def merge_lyrics(self, lyrics):
        i = 0
        for bar in self.barlist:
            for obj in bar.obj_list:
                if isinstance(obj, BarNote):
                    obj.add_lyric(lyrics.barlist[i])
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
                    b += obj.base_scaling[0]
                    s *= obj.base_scaling[1]
            elif isinstance(obj, BarBackup):
                break
        return BarBackup((b,s))

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
            new_voice.obj_list.pop(0)
        if not new_voice.is_skip():
            self.add(new_voice.create_backup())
            for nv in new_voice.obj_list:
                    self.add(nv)


class BarMus():
    """ Common class for notes and rests. """
    def has_attr(self):
        return False


class BarNote(BarMus):
    """ object to keep track of note parameters """
    def __init__(self, note, voice=1):
        self.note = note
        self.pitch = note.pitch
        self.base_note = getNoteName(note.pitch.note)
        self.alter = note.pitch.alter*2
        if note.duration:
            self.duration = note.duration
            self.base_scaling = note.duration.base_scaling
        self.type = None
        self.tuplet = 0
        self.dot = 0
        self.tie = 0
        self.grace = (0,0)
        self.tremolo = ('',0)
        self.voice = voice
        self.staff = 0
        self.chord = False
        self.skip = False
        self.slur = None
        self.artic = None
        self.ornament = None
        self.other_notation = None
        self.fingering = None
        self.lyric = None

    def set_duration(self, duration, durval=0):
        self.duration = duration
        self.base_scaling = duration.base_scaling
        self.dot = 0
        if durval:
            self.type = durval2type(durval)

    def set_durtype(self, durval):
        self.type = durval2type(durval)

    def set_octave(self, relative, prev_pitch=None):
        if relative:
            self.pitch.makeAbsolute(prev_pitch)

    def set_tuplet(self, fraction, ttype):
        self.tuplet = fraction
        self.ttype = ttype

    def set_staff(self, staff):
        self.staff = staff

    def set_tie(self, tie_type):
        self.tie = tie_type

    def add_dot(self):
        self.dot += 1

    def set_slur(self, slur_type):
        self.slur = slur_type

    def add_articulation(self, art_name):
        self.artic = art_name

    def add_ornament(self, ornament):
        self.ornament = ornament

    def set_grace(self, slash):
        self.grace = (1,slash)

    def set_tremolo(self, trem_type, duration=False):
        if duration:
            self.tremolo = (trem_type, dur2lines(duration))
        else:
            self.tremolo = (trem_type, self.tremolo[1])

    def add_other_notation(self, other):
        self.other_notation = other

    def add_fingering(self, finger_nr):
        self.fingering = finger_nr

    def add_lyric(self, text):
        self.lyric = text


class BarRest(BarMus):
    """ object to keep track of different rests and skips """
    def __init__(self, rest, voice=1, show_type=True, skip=False, pos=0):
        self.note = rest
        if rest.duration:
            self.duration = rest.duration
            self.base_scaling = rest.duration.base_scaling
        self.show_type = show_type
        self.type = None
        self.skip = skip
        self.tuplet = 0
        self.dot = 0
        self.pos = pos
        self.voice = voice
        self.staff = 0
        self.chord = False

    def set_duration(self, duration, durval=0, durtype=None):
        self.duration = duration
        self.base_scaling = duration.base_scaling
        if durval:
            if self.show_type:
                self.type = durval2type(durval)
            else:
                self.type = None

    def set_durtype(self, durval):
        if self.show_type:
            self.type = durval2type(durval)

    def add_dot(self):
        self.dot += 1

    def set_staff(self, staff):
        self.staff = staff


class BarAttr():
    """ object that keep track of bar attributes, e.g. time sign, clef, key etc """
    def __init__(self):
        self.key = 0
        self.time = 0
        self.clef = 0
        self.mode = ''
        self.divs = 0
        self.barline = ''
        self.repeat = None
        self.staves = 0
        self.multiclef = []
        self.tempo = None

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
        if self.key != 0:
            check = True
        elif self.time != 0:
            check = True
        elif self.clef != 0:
            check = True
        elif self.divs != 0:
            check = True
        return check


class BarBackup():
    """ Object that stores duration for backup """
    def __init__(self, base_scaling):
        self.base_scaling = base_scaling


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
    """
    To add a clef look up the clef name in LilyPond
    and the corresponding definition in musicXML.
    Add it to the python dictionary below.
    """
    clef_dict = {
    "treble": ('G',2,0), "violin": ('G',2,0), "G": ('G',2,0),
    "bass": ('F',4,0), "F": ('F',4,0),
    "alto": ('C',3,0), "C": ('C',3,0),
    "tenor": ('C',4,0), "treble_8": ('G',2,-1),
    "bass_8": ('F',4,-1), "treble^8": ('G',2,1),
    "bass^8": ('F',4,1), "percussion": ('percussion',0,0),
    "tab": ('TAB',5,0), "soprano": ('C',1,0),
    "mezzosoprano": ('C',2,0),
    "baritone": ('C',5,0),
    "varbaritone": ('F',3,0)
    }
    return clef_dict[clefname]

def getNoteName(index):
    noteNames = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    return noteNames[index]

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
    try:
        note_num = base_list.index(note_name)
    except ValueError:
        print(note_name+" isn't recognised as a supported pitch name.")
        note_num = 0
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
    if dur == 8:
        return 1
    elif dur == 16:
        return 2
    elif dur == 32:
        return 3
    else:
        return 0

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

def artic_token2xml_name(art_token):
    """
    From Articulations in ly.music.items.
    Grouped as articulations, ornaments and others.

    To add an articulation look up the name or abbreviation
    in LilyPond and the corresponding node name in musicXML.
    Add it to the python dictionary below.
    """
    artic_dict = {
    ".": "staccato", "-": "tenuto", ">": "accent",
    "_": "detached-legato", "!": "staccatissimo",
    "\\staccatissimo": "staccatissimo"
    }
    ornaments = ['\\trill', '\\prall', '\\mordent', '\\turn']
    others = ['\\fermata']
    try:
        return artic_dict[art_token]
    except KeyError:
        if art_token in ornaments:
            return "ornament"
        elif art_token in others:
            return "other"
        else:
            return False

def calc_trem_dur(repeats, base_scaling, duration):
    """ Calculate tremolo duration from number of
    repeats and initial duration. """
    base = base_scaling[0]
    scale = base_scaling[1]
    new_base = base * repeats
    new_type = durval2type(str(duration/repeats))
    return (new_base, scale), new_type
