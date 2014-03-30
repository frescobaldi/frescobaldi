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
Export to Music XML
Uses xml.etree to create the XML document
"""

from __future__ import unicode_literals

import sys
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


import ly.pkginfo


class create_musicXML():
    """ creates the XML-file from the source code according to the Music XML standard """

    def __init__(self):
        """ creates the basic structure of the XML without any music
        TODO:
        set doctype
        """
        self.root = etree.Element("score-partwise", version="3.0")
        self.tree = etree.ElementTree(self.root)
        identification = etree.SubElement(self.root, "identification")
        encoding = etree.SubElement(identification, "encoding")
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

    def create_part(self, name):
        """ create a new part """
        part = etree.SubElement(self.partlist, "score-part", id="P"+str(self.part_count))
        partname = etree.SubElement(part, "part-name")
        partname.text = name
        self.current_part = etree.SubElement(self.root, "part", id="P"+str(self.part_count))
        self.part_count +=1
        self.bar_nr = 1

    def create_measure(self):
        """ create new measure """
        self.current_bar = etree.SubElement(self.current_part, "measure", number=str(self.bar_nr))
        self.bar_nr +=1

    ##
    # High-level node creation
    ##

    def new_note(self, grace, pitch, base_scaling, voice, durtype, divs, dot, chord):
        """ create all nodes needed for a note. """
        self.create_note()
        if grace[0]:
            self.add_grace(grace[1])
        if chord:
            self.add_chord()
        self.add_pitch(pitch[0], pitch[1], pitch[2])
        if not grace[0]:
            self.add_div_duration(self.count_duration(base_scaling, divs, dot))
        self.add_voice(voice)
        self.add_duration_type(durtype)
        if dot:
            for i in range(dot):
                self.add_dot()
        if pitch[1]:
            self.add_accidental(pitch[1])

    def tuplet_note(self, fraction, base_scaling, ttype, divs):
        """ convert current note to tuplet """
        base = base_scaling[0]
        scaling = base_scaling[1]
        a = divs*4*fraction.denominator
        b = (1/base)*fraction.numerator
        duration = (a/b)*scaling
        self.change_div_duration(duration)
        self.add_time_modify(fraction)
        if ttype:
            self.add_notations()
            self.add_tuplet_type(ttype)

    def tie_note(self, tie_type):
        self.add_tie(tie_type)
        self.add_notations()
        self.add_tied(tie_type)

    def new_rest(self, base_scaling, durtype, divs, pos, dot, voice):
        """ create all nodes needed for a rest. """
        self.create_note()
        self.add_rest(pos)
        self.add_div_duration(self.count_duration(base_scaling, divs, dot))
        self.add_voice(voice)
        if durtype:
            self.add_duration_type(durtype)
        if dot:
            for i in range(dot):
                self.add_dot()

    def new_skip(self, base_scaling, divs):
        base = base_scaling[0]
        scaling = base_scaling[1]
        duration = divs*4*base*scaling
        self.add_skip(duration)

    def new_bar_attr(self, clef, mustime, key, mode, divs):
        """ create all bar attributes set. """
        self.create_bar_attr()
        if divs:
            self.add_divisions(divs)
        if key>=0:
            self.add_key(key, mode)
        if mustime:
            self.add_time(mustime)
        if clef:
            sign, line, octch = clef
            self.add_clef(sign, line, oct_ch=octch)

    def new_backup(self, base_scaling, divs):
        self.add_backup(self.count_duration(base_scaling, divs, 0))

    def create_new_node(self, parentnode, nodename, txt):
        """ The Music XML language is extensive.
        This function can be used to create
        a non basic node not covered elsewhere in this script.
        TODO: add attributes
        """
        new_node = etree.SubElement(parentnode, nodename)
        new_node.text = str(txt)

    ##
    # Help functions
    ##

    def count_duration(self, base_scaling, divs, dot):
        base = base_scaling[0]
        scaling = base_scaling[1]
        if dot:
            import math
            den = int(math.pow(2,dot))
            num = int(math.pow(2,dot+1)-1)
            a = divs*4*num
            b = (1/base)*den
            duration = a/b
        else:
            duration = divs*4*base
        duration = duration * scaling
        return int(duration)


    ##
    # Low-level node creation
    ##

    def create_note(self):
        """ create new note """
        self.current_note = etree.SubElement(self.current_bar, "note")
        self.current_notation = None
        self.current_ornaments = None

    def add_pitch(self, step, alter, octave):
        """ create new pitch """
        pitch = etree.SubElement(self.current_note, "pitch")
        stepnode = etree.SubElement(pitch, "step")
        stepnode.text = str(step)
        if alter:
            altnode = etree.SubElement(pitch, "alter")
            altnode.text = str(alter)
        octnode = etree.SubElement(pitch, "octave")
        octnode.text = str(octave)

    def add_accidental(self, alter):
        """ create accidental """
        acc = etree.SubElement(self.current_note, "accidental")
        if alter == 1:
            acc.text = "sharp"
        elif alter == 2:
            acc.text = "double-sharp"
        elif alter == -1:
            acc.text = "flat"
        elif alter == -2:
            acc.text = "flat-flat"

    def add_rest(self, pos):
        """ create rest """
        restnode = etree.SubElement(self.current_note, "rest")
        if pos:
            step = etree.SubElement(restnode, "display-step")
            octave = etree.SubElement(restnode, "display-octave")
            step.text = str(pos[0])
            octave.text = str(pos[1])

    def add_skip(self, duration, forward=True):
        if forward:
            skip = etree.SubElement(self.current_bar, "forward")
        else:
            skip = etree.SubElement(self.current_bar, "backward")
        dura_node = etree.SubElement(skip, "duration")
        dura_node.text = str(duration)

    def add_div_duration(self, divdur):
        """ create new duration """
        self.duration = etree.SubElement(self.current_note, "duration")
        self.duration.text = str(divdur)

    def change_div_duration(self, newdura):
        """ set new duration when tuplet """
        self.duration.text = str(newdura)

    def add_duration_type(self, durtype):
        """ create new type """
        typenode = etree.SubElement(self.current_note, "type")
        typenode.text = str(durtype)

    def add_dot(self):
        """ create a dot """
        etree.SubElement(self.current_note, "dot")

    def add_tie(self, tie_type):
        """ create node tie (used for sound of tie) """
        etree.SubElement(self.current_note, "tie", type=tie_type)

    def add_grace(self, slash):
        """ create grace node """
        if slash:
            etree.SubElement(self.current_note, "grace", slash="yes")
        else:
            etree.SubElement(self.current_note, "grace")

    def add_notations(self):
        if not self.current_notation:
            self.current_notation = etree.SubElement(self.current_note, "notations")

    def add_tied(self, tie_type):
        """ create node tied (used for notation of tie) """
        etree.SubElement(self.current_notation, "tied", type=tie_type)

    def add_time_modify(self, fraction):
        """ create time modification """
        timemod_node = etree.SubElement(self.current_note, "time-modification")
        actual_notes = etree.SubElement(timemod_node, "actual-notes")
        actual_notes.text = str(fraction.numerator)
        norm_notes = etree.SubElement(timemod_node, "normal-notes")
        norm_notes.text = str(fraction.denominator)

    def add_tuplet_type(self, ttype):
        """ create tuplet with type attribute """
        etree.SubElement(self.current_notation, "tuplet", type=ttype)

    def add_ornaments(self):
        if not self.current_ornaments:
            self.add_notations()
            self.current_ornament = etree.SubElement(self.current_notation, "ornaments")

    def add_tremolo(self, trem_type, lines):
        self.add_ornaments()
        trem_node = etree.SubElement(self.current_ornament, "tremolo", type=trem_type)
        trem_node.text = str(lines)

    def create_bar_attr(self):
        """ create node attributes """
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
        linenode = etree.SubElement(clefnode, "line")
        linenode.text = str(line)
        if oct_ch:
            octchnode = etree.SubElement(clefnode, "clef-octave-change")
            octchnode.text = str(oct_ch)

    def add_barline(self, bl_type, repeat=None):
        barnode = etree.SubElement(self.current_bar, "barline", location="right")
        barstyle = etree.SubElement(barnode, "bar-style")
        barstyle.text = bl_type
        if repeat:
            repeatnode = etree.SubElement(barnode, "repeat", direction=repeat)

    def add_backup(self, duration):
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
        stavesnode = etree.SubElement(self.bar_attr, "staves")
        stavesnode.text = str(staves)

    def add_chord(self):
        etree.SubElement(self.current_note, "chord")


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
        """ add indent and linebreaks to the created XML tree """
        import ly.etreeutil
        ly.etreeutil.indent(self.root, indent)

    def tostring(self, encoding='UTF-8'):
        """ output etree as a XML document """
        return etree.tostring(self.root, encoding=encoding, method="xml")

    def write(self, file, encoding='UTF-8'):
        """ write XML to a file (file obj or filename) """
        self.tree.write(file, encoding=encoding, xml_declaration=True, method="xml")


