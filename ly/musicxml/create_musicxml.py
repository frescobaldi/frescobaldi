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
Uses xml.etree to create a Music XML document.

Example::

    musxml = create_musicxml.CreateMusicXML()
    musxml.create_part()
    musxml.create_measure(divs=1)
    musxml.new_note('C', 4, 'whole', 4)
    xml = musxml.musicxml()
    xml.write(filename)

"""

from __future__ import unicode_literals
from __future__ import division

import sys
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


import ly.pkginfo

from .midi_sound_map import midi_sound_map

class CreateMusicXML():
    """ Creates the XML nodes according to the Music XML standard."""

    def __init__(self):
        """Creates the basic structure of the XML without any music."""
        self.root = etree.Element("score-partwise", version="3.0")
        self.tree = etree.ElementTree(self.root)
        self.score_info = etree.SubElement(self.root, "identification")
        encoding = etree.SubElement(self.score_info, "encoding")
        software = etree.SubElement(encoding, "software")
        software.text = ly.pkginfo.name + " " + ly.pkginfo.version
        encoding_date = etree.SubElement(encoding, "encoding-date")
        import datetime
        encoding_date.text = str(datetime.date.today())
        self.partlist = etree.SubElement(self.root, "part-list")
        self.part_count = 1

    ##
    # Building the basic Elements
    ##

    def create_title(self, title):
        """Create score title."""
        mov_title = etree.Element("movement-title")
        mov_title.text = title
        self.root.insert(0, mov_title)

    def create_score_info(self, tag, info, attr={}):
        """Create score info."""
        info_node = etree.SubElement(self.score_info, tag, attr)
        info_node.text = info

    def create_partgroup(self, gr_type, num, name=None, abbr=None, symbol=None):
        """Create a new part group."""
        attr_dict = {"type": gr_type, "number": str(num)}
        partgroup = etree.SubElement(self.partlist, "part-group", attr_dict)
        if name:
            group_name = etree.SubElement(partgroup, "group-name")
            group_name.text = name
        if abbr:
            group_abbr = etree.SubElement(partgroup, "group-abbreviation")
            group_abbr.text = abbr
        if symbol:
            group_symbol = etree.SubElement(partgroup, "group-symbol")
            group_symbol.text = symbol

    def create_part(self, name="unnamed", abbr=False, midi=False):
        """Create a new part """
        strnr = str(self.part_count)
        part = etree.SubElement(self.partlist, "score-part", id="P"+strnr)
        partname = etree.SubElement(part, "part-name")
        partname.text = name
        if abbr:
            partabbr = etree.SubElement(part, "part-abbreviation")
            partabbr.text = abbr
        if midi:
            scoreinstr = etree.SubElement(part, "score-instrument", id="P"+strnr+"-I"+strnr)
            instrname = etree.SubElement(scoreinstr, "instrument-name")
            instrname.text = midi

            if midi in midi_sound_map and midi_sound_map[midi]:
                instrsound = etree.SubElement(scoreinstr, "instrument-sound")
                instrsound.text = midi_sound_map[midi]

            midiinstr = etree.SubElement(part, "midi-instrument", id="P"+strnr+"-I"+strnr)
            midich = etree.SubElement(midiinstr, "midi-channel")
            midich.text = strnr
            midiname = etree.SubElement(midiinstr, "midi-name")
            midiname.text = midi
        self.current_part = etree.SubElement(self.root, "part", id="P"+strnr)
        self.part_count += 1
        self.bar_nr = 1

    def create_measure(self, pickup = False, **bar_attrs):
        """Create new measure """
        if pickup and self.bar_nr == 1:
            self.bar_nr = 0
        self.current_bar = etree.SubElement(self.current_part, "measure", number=str(self.bar_nr))
        self.bar_nr +=1
        if bar_attrs:
            self.new_bar_attr(**bar_attrs)

    ##
    # High-level node creation
    ##

    def new_note(self, step, octave, durtype, divdur, alter=0,
                 acc_token=0, voice=1, dot=0, chord=0, grace=(0, 0), stem_dir=0):
        """Create all nodes needed for a normal note. """
        self.create_note()
        if grace[0]:
            self.add_grace(grace[1])
        if chord:
            self.add_chord()
        self.add_pitch(step, alter, octave)
        if not grace[0]:
            self.add_div_duration(divdur)
        self.add_voice(voice)
        self.add_duration_type(durtype)
        if dot:
            for i in range(dot):
                self.add_dot()
        if alter or acc_token:
            if acc_token == '!': # cautionary
                self.add_accidental(alter, caut=True)
            elif acc_token == '?': # parentheses
                self.add_accidental(alter, parenth=True)
            else:
                self.add_accidental(alter)
        if stem_dir:
            self.set_stem_dir(stem_dir)

    def new_unpitched_note(self, step, octave, durtype, divdur, voice=1,
                            dot=0, chord=0, grace=(0, 0)):
        """Create all nodes needed for an unpitched note. """
        self.create_note()
        if grace[0]:
            self.add_grace(grace[1])
        if chord:
            self.add_chord()
        self.add_unpitched(step, octave)
        if not grace[0]:
            self.add_div_duration(divdur)
        self.add_duration_type(durtype)
        self.add_voice(voice)
        if dot:
            for i in range(dot):
                self.add_dot()

    def tuplet_note(self, fraction, bs, ttype, nr, divs, atyp='', ntyp=''):
        """Convert current note to tuplet """
        base = self.mult * bs[0]
        scaling = bs[1]
        a = divs*4*fraction[1]
        b = (1/base)*fraction[0]
        duration = (a/b)*scaling
        self.change_div_duration(duration)
        from fractions import Fraction
        self.mult = Fraction(fraction[1], fraction[0])
        timemod_node = self.get_time_modify()
        if timemod_node:
            self.adjust_time_modify(timemod_node, fraction)
        else:
            self.add_time_modify(fraction)
        if ttype:
            self.add_notations()
            if atyp and ttype != "stop":
                self.add_tuplet_type(nr, ttype, fraction[0], atyp, fraction[1], ntyp)
            else:
                self.add_tuplet_type(nr, ttype)

    def tie_note(self, tie_type):
        self.add_tie(tie_type)
        self.add_notations()
        self.add_tied(tie_type)

    def new_rest(self, duration, durtype, pos, dot, voice):
        """Create all nodes needed for a rest. """
        self.create_note()
        if pos:
            self.add_rest_w_pos(pos[0], pos[1])
        else:
            self.add_rest()
        self.add_div_duration(duration)
        self.add_voice(voice)
        if durtype:
            self.add_duration_type(durtype)
        if dot:
            for i in range(dot):
                self.add_dot()

    def new_articulation(self, artic):
        """Add specified articulation. """
        self.add_notations()
        self.add_articulations()
        self.add_named_artic(artic)

    def new_simple_ornament(self, ornament):
        """Add specified ornament. """
        self.add_notations()
        self.add_ornaments()
        func_call = getattr(self, 'add_'+ornament)
        func_call()

    def new_adv_ornament(self, ornament, args):
        """Add more complex ornament."""
        self.add_notations()
        self.add_ornaments()
        if ornament == "wavy-line":
            self.add_wavyline(args['type'])

    def new_bar_attr(self, clef=0, mustime=0, key=None, mode=0, divs=0, multirest=0):
        """Create all bar attributes set. """
        self.create_bar_attr()
        if divs:
            self.add_divisions(divs)
        if key is not None:
            self.add_key(key, mode)
        if mustime:
            self.add_time(mustime)
        if clef:
            sign, line, octch = clef
            self.add_clef(sign, line, oct_ch=octch)
        if multirest:
            self.add_bar_style(multirest)

    def create_tempo(self, words, metronome, sound, dots):
        self.add_direction()
        if words:
            self.add_dirwords(words)
        if metronome:
            self.add_metron_dir(metronome[0], metronome[1], dots)
            self.add_sound_dir(sound)

    def create_new_node(self, parentnode, nodename, txt):
        """ The Music XML language is extensive.
        This function can be used to create
        a non basic node not covered elsewhere in this script.

        TODO: add attributes
        """
        new_node = etree.SubElement(parentnode, nodename)
        new_node.text = str(txt)


    ##
    # Low-level node creation
    ##

    def add_creator(self, creator, name):
        """Add creator to score info."""
        attr = {'type': creator }
        self.create_score_info("creator", name, attr)

    def add_rights(self, rights, type=None):
        """Add rights to score info."""
        attr = {'type': type} if type else {}
        self.create_score_info("rights", rights, attr)

    def create_note(self):
        """Create new note."""
        self.current_note = etree.SubElement(self.current_bar, "note")
        self.current_notation = None
        self.current_artic = None
        self.current_ornament = None
        self.current_tech = None

    def add_pitch(self, step, alter, octave):
        """Create new pitch."""
        pitch = etree.SubElement(self.current_note, "pitch")
        stepnode = etree.SubElement(pitch, "step")
        stepnode.text = str(step)
        if alter:
            altnode = etree.SubElement(pitch, "alter")
            altnode.text = str(alter)
        octnode = etree.SubElement(pitch, "octave")
        octnode.text = str(octave)

    def add_unpitched(self, step, octave):
        """Create unpitched."""
        unpitched = etree.SubElement(self.current_note, "unpitched")
        stepnode = etree.SubElement(unpitched, "display-step")
        stepnode.text = str(step)
        octnode = etree.SubElement(unpitched, "display-octave")
        octnode.text = str(octave)

    def add_accidental(self, alter, caut=False, parenth=False):
        """Create accidental."""
        attrib = {}
        if caut:
            attrib['cautionary'] = 'yes'
        if parenth:
            attrib['parentheses'] = 'yes'
        acc = etree.SubElement(self.current_note, "accidental", attrib)
        acc_dict = {
        0: 'natural',
        1: 'sharp', -1: 'flat',
        2: 'sharp-sharp', -2: 'flat-flat',
        0.5: 'natural-up', -0.5: 'natural-down',
        1.5: 'sharp-up', -1.5: 'flat-down'
        }
        acc.text = acc_dict[alter]

    def set_stem_dir(self, dir):
        stem_dir = etree.SubElement(self.current_note, "stem")
        stem_dir.text = dir

    def add_rest(self):
        """Create rest."""
        etree.SubElement(self.current_note, "rest")

    def add_rest_w_pos(self, step, octave):
        """Create rest with display position."""
        restnode = etree.SubElement(self.current_note, "rest")
        stepnode = etree.SubElement(restnode, "display-step")
        octnode = etree.SubElement(restnode, "display-octave")
        stepnode.text = str(step)
        octnode.text = str(octave)

    def add_skip(self, duration, forward=True):
        if forward:
            skip = etree.SubElement(self.current_bar, "forward")
        else:
            skip = etree.SubElement(self.current_bar, "backward")
        dura_node = etree.SubElement(skip, "duration")
        dura_node.text = str(duration)

    def add_div_duration(self, divdur):
        """Create new duration """
        self.duration = etree.SubElement(self.current_note, "duration")
        self.duration.text = str(divdur)
        self.mult = 1

    def change_div_duration(self, newdura):
        """Set new duration when tuplet """
        self.duration.text = str(newdura)

    def add_duration_type(self, durtype):
        """Create new type """
        typenode = etree.SubElement(self.current_note, "type")
        typenode.text = str(durtype)

    def add_dot(self):
        """Create a dot """
        etree.SubElement(self.current_note, "dot")

    def add_beam(self, nr, beam_type):
        """Add beam. """
        beam_node = etree.SubElement(self.current_notation, "beam", number=str(nr))
        beam_node.text = beam_type

    def add_tie(self, tie_type):
        """Create node tie (used for sound of tie) """
        # A tie must be directly after a duration
        insert_at = get_tag_index(self.current_note, "duration") + 1
        tie_element = etree.Element("tie", type=tie_type)
        self.current_note.insert(insert_at, tie_element)

    def add_grace(self, slash):
        """Create grace node """
        if slash:
            etree.SubElement(self.current_note, "grace", slash="yes")
        else:
            etree.SubElement(self.current_note, "grace")

    def add_notations(self):
        if not self.current_notation:
            self.current_notation = etree.SubElement(self.current_note, "notations")

    def add_tied(self, tie_type):
        """Create node tied (used for notation of tie) """
        etree.SubElement(self.current_notation, "tied", type=tie_type)

    def add_time_modify(self, fraction):
        """Create time modification """
        index = get_tag_index(self.current_note, "accidental")
        if index == -1:
            index = get_tag_index(self.current_note, "dot")
        if index == -1:
            index = get_tag_index(self.current_note, "type")
        timemod_node = etree.Element("time-modification")
        actual_notes = etree.SubElement(timemod_node, "actual-notes")
        actual_notes.text = str(fraction[0])
        norm_notes = etree.SubElement(timemod_node, "normal-notes")
        norm_notes.text = str(fraction[1])
        self.current_note.insert(index + 1, timemod_node)

    def get_time_modify(self):
        """Check if time-modification node already exists."""
        return self.current_note.find("time-modification")

    def adjust_time_modify(self, timemod_node, fraction):
        """Adjust existing time-modification node."""
        actual_notes = timemod_node.find("actual-notes")
        an = int(actual_notes.text) * fraction[0]
        actual_notes.text = str(an)
        norm_notes = timemod_node.find("normal-notes")
        nn = int(norm_notes.text) * fraction[1]
        norm_notes.text = str(nn)

    def add_tuplet_type(self, nr, ttype, actnr=0, acttype='', normnr=0, normtype=''):
        """Create tuplet with type attribute """
        tuplnode = etree.SubElement(self.current_notation, "tuplet",
                                    {'number': str(nr), 'type': ttype })
        if actnr:
            actnode = etree.SubElement(tuplnode, "tuplet-actual")
            atn = etree.SubElement(actnode, "tuplet-number")
            atn.text = str(actnr)
            att = etree.SubElement(actnode, "tuplet-type")
            if not acttype:
                acttype = self.current_note.find("type").text
            att.text = acttype
        if normnr:
            normnode = etree.SubElement(tuplnode, "tuplet-normal")
            ntn = etree.SubElement(normnode, "tuplet-number")
            ntn.text = str(normnr)
            ntt = etree.SubElement(normnode, "tuplet-type")
            if not normtype:
                normtype = self.current_note.find("type").text
            ntt.text = normtype

    def add_slur(self, nr, sl_type):
        """Add slur. """
        self.add_notations()
        etree.SubElement(self.current_notation, "slur", {'number': str(nr), 'type': sl_type })

    def add_named_notation(self, notate):
        """Fermata, etc. """
        self.add_notations()
        etree.SubElement(self.current_notation, notate)

    def add_articulations(self):
        """Common function for creating all types of articulations. """
        if not self.current_artic:
            self.current_artic = etree.SubElement(self.current_notation, "articulations")

    def add_named_artic(self, artic):
        """Add articulation with specified name. """
        etree.SubElement(self.current_artic, artic)

    def add_ornaments(self):
        if not self.current_ornament:
            self.add_notations()
            self.current_ornament = etree.SubElement(self.current_notation, "ornaments")

    def add_tremolo(self, trem_type, lines):
        self.add_ornaments()
        trem_node = etree.SubElement(self.current_ornament, "tremolo", type=trem_type)
        trem_node.text = str(lines)

    def add_trill(self):
        etree.SubElement(self.current_ornament, "trill-mark")

    def add_turn(self):
        etree.SubElement(self.current_ornament, "turn")

    def add_mordent(self):
        etree.SubElement(self.current_ornament, "mordent")

    def add_prall(self):
        etree.SubElement(self.current_ornament, "inverted-mordent")

    def add_wavyline(self, end_type):
        self.add_ornaments
        etree.SubElement(self.current_ornament, "wavy-line", type=end_type)

    def add_gliss(self, linetype, endtype, nr):
        nodedict = { "line-type": linetype, "number": str(nr), "type": endtype }
        self.add_notations()
        etree.SubElement(self.current_notation, "glissando", nodedict)

    def add_technical(self):
        if not self.current_tech:
            self.add_notations()
            self.current_tech = etree.SubElement(self.current_notation, "technical")

    def add_fingering(self, finger_nr):
        self.add_technical()
        fing_node = etree.SubElement(self.current_tech, "fingering")
        fing_node.text = str(finger_nr)

    def create_bar_attr(self):
        """Create node attributes """
        self.bar_attr = etree.SubElement(self.current_bar, "attributes")

    def add_divisions(self, div):
        division = etree.SubElement(self.bar_attr, "divisions")
        division.text = str(div)

    def add_key(self, key, mode):
        keynode = etree.SubElement(self.bar_attr, "key")
        fifths = etree.SubElement(keynode, "fifths")
        fifths.text = str(key)
        modenode = etree.SubElement(keynode, "mode")
        modenode.text = str(mode)

    def add_time(self, timesign):
        if len(timesign)==3:
            timenode = etree.SubElement(self.bar_attr, "time", symbol=timesign[2])
        else:
            timenode = etree.SubElement(self.bar_attr, "time")
        beatnode = etree.SubElement(timenode, "beats")
        beatnode.text = str(timesign[0])
        typenode = etree.SubElement(timenode, "beat-type")
        typenode.text = str(timesign[1])

    def add_clef(self, sign, line, nr=0, oct_ch=0):
        if nr:
            clefnode = etree.SubElement(self.bar_attr, "clef", number=str(nr))
        else:
            clefnode = etree.SubElement(self.bar_attr, "clef")
        signnode = etree.SubElement(clefnode, "sign")
        signnode.text = str(sign)
        if line:
            linenode = etree.SubElement(clefnode, "line")
            linenode.text = str(line)
        if oct_ch:
            octchnode = etree.SubElement(clefnode, "clef-octave-change")
            octchnode.text = str(oct_ch)

    def add_bar_style(self, multirest=None):
        bar_style = etree.SubElement(self.bar_attr, "measure-style")
        if multirest:
            multirestnode = etree.SubElement(bar_style, "multiple-rest")
            multirestnode.text = str(multirest)

    def new_system(self, force_break):
        etree.SubElement(self.current_bar, "print", {'new-system':force_break})

    def add_barline(self, bl_type, repeat=None):
        barnode = etree.SubElement(self.current_bar, "barline", location="right")
        barstyle = etree.SubElement(barnode, "bar-style")
        barstyle.text = bl_type
        if repeat:
            repeatnode = etree.SubElement(barnode, "repeat", direction=repeat)

    def add_backup(self, duration):
        if duration <= 0:
            return
        backupnode = etree.SubElement(self.current_bar, "backup")
        durnode = etree.SubElement(backupnode, "duration")
        durnode.text = str(duration)

    def add_voice(self, voice):
        voicenode = etree.SubElement(self.current_note, "voice")
        voicenode.text = str(voice)

    def add_staff(self, staff):
        staffnode = etree.SubElement(self.current_note, "staff")
        staffnode.text = str(staff)

    def add_staves(self, staves):
        index = get_tag_index(self.bar_attr, "time")
        stavesnode = etree.Element("staves")
        stavesnode.text = str(staves)
        self.bar_attr.insert(index + 1, stavesnode)

    def add_chord(self):
        etree.SubElement(self.current_note, "chord")

    def add_direction(self, pos="above"):
        self.direction = etree.SubElement(self.current_bar, "direction", placement=pos)

    def add_dynamic_mark(self, dyn):
        """Add specified dynamic mark."""
        direction = etree.SubElement(self.current_bar, "direction", placement='below')
        dirtypenode = etree.SubElement(direction, "direction-type")
        dyn_node = etree.SubElement(dirtypenode, "dynamics")
        dynexpr_node = etree.SubElement(dyn_node, dyn)

    def add_dynamic_wedge(self, wedge_type):
        """Add dynamic wedge/hairpin."""
        direction = etree.SubElement(self.current_bar, "direction", placement='below')
        dirtypenode = etree.SubElement(direction, "direction-type")
        dyn_node = etree.SubElement(dirtypenode, "wedge", type=wedge_type)

    def add_dynamic_text(self, text):
        """Add dynamic text."""
        direction = etree.SubElement(self.current_bar, "direction", placement='below')
        dirtypenode = etree.SubElement(direction, "direction-type")
        dyn_node = etree.SubElement(dirtypenode, "words")
        dyn_node.attrib['font-style'] = 'italic'
        dyn_node.text = text

    def add_dynamic_dashes(self, text):
        """Add dynamics dashes."""
        direction = etree.SubElement(self.current_bar, "direction", placement='below')
        dirtypenode = etree.SubElement(direction, "direction-type")
        dyn_node = etree.SubElement(dirtypenode, "dashes", type=text)

    def add_octave_shift(self, plac, octdir, size):
        """Add octave shift."""
        oct_dict = {"type": octdir, "size": str(size) }
        direction = etree.SubElement(self.current_bar, "direction", placement=plac)
        dirtypenode = etree.SubElement(direction, "direction-type")
        dyn_node = etree.SubElement(dirtypenode, "octave-shift", oct_dict)

    def add_dirwords(self, words):
        """Add words in direction, e. g. a tempo mark."""
        if self.current_bar.find('direction') == None:
            self.add_direction()
        dirtypenode = etree.SubElement(self.direction, "direction-type")
        wordsnode = etree.SubElement(dirtypenode, "words")
        wordsnode.text = words

    def add_mark(self, mark):
        """Add rehearsal mark in direction"""
        if self.current_bar.find('direction') == None:
            self.add_direction()
        dirtypenode = etree.SubElement(self.direction, "direction-type")
        rehearsalnode = etree.SubElement(dirtypenode, "rehearsal")
        rehearsalnode.text = mark

    def add_metron_dir(self, unit, beats, dots):
        dirtypenode = etree.SubElement(self.direction, "direction-type")
        metrnode = etree.SubElement(dirtypenode, "metronome")
        bunode = etree.SubElement(metrnode, "beat-unit")
        bunode.text = unit
        if dots:
            for d in range(dots):
                etree.SubElement(metrnode, "beat-unit-dot")
        pmnode = etree.SubElement(metrnode, "per-minute")
        pmnode.text = str(beats)

    def add_sound_dir(self, midi_tempo):
        # FIXME: remove the int conversion once LilyPond accepts decimal tempo
        soundnode = etree.SubElement(self.direction, "sound", tempo=str(int(midi_tempo)))

    def add_lyric(self, txt, syll, nr, ext=False):
        """ Add lyric element. """
        lyricnode = etree.SubElement(self.current_note, "lyric", number=str(nr))
        syllnode = etree.SubElement(lyricnode, "syllabic")
        syllnode.text = syll
        txtnode = etree.SubElement(lyricnode, "text")
        txtnode.text = txt
        if ext:
            etree.SubElement(lyricnode, "extend")


    ##
    # Create the XML document
    ##

    def musicxml(self, prettyprint=True):
        xml = MusicXML(self.tree)
        if prettyprint:
            xml.indent("  ")
        return xml


class MusicXML(object):
    """Represent a generated MusicXML tree."""
    def __init__(self, tree):
        self.tree = tree
        self.root = tree.getroot()

    def indent(self, indent="  "):
        """Add indent and linebreaks to the created XML tree."""
        import ly.etreeutil
        ly.etreeutil.indent(self.root, indent)

    def tostring(self, encoding='UTF-8'):
        """Output etree as a XML document."""
        return etree.tostring(self.root, encoding=encoding, method="xml")

    def write(self, file, encoding='UTF-8', doctype=True):
        """Write XML to a file (file obj or filename)."""
        def write(f):
            if doctype:
                f.write((xml_decl_txt + "\n").format(encoding=encoding).encode(encoding))
                f.write((doctype_txt + "\n").encode(encoding))
                self.tree.write(f, encoding=encoding, xml_declaration=False)
            else:
                self.tree.write(f, encoding=encoding, xml_declaration=True, method="xml")
        if hasattr(file, 'write'):
            write(file)
            # do not close if it already was a file object
        else:
            # it is not a file object
            with open(file, 'wb') as f:
                write(f)


def get_tag_index(node, tag):
    """Return the (first) index of tag in node.

    If tag is not found, -1 is returned.
    """
    for i, elem in enumerate(list(node)):
        if elem.tag == tag:
            return i
    return -1


xml_decl_txt = """<?xml version="1.0" encoding="{encoding}"?>"""

doctype_txt = """<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">"""
