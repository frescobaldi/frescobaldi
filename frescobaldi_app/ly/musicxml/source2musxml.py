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
Parsing source to convert to XML
"""

from __future__ import unicode_literals

import ly.lex

from . import create_musicxml
from . import ly2xml_mediator


class parse_source():
    """ creates the XML-file from the source code according to the Music XML standard """

    def __init__(self):
        self.musxml = create_musicxml.create_musicXML()
        self.mediator = ly2xml_mediator.mediator()
        self.prev_command = ''
        self.pitch_mode = 'abs'
        self.varname = ''
        self.can_create_sect = True
        self.tuplet = False
        self.scale = ''
        self.grace_seq = False
        self.new = False
        self.context = False
        self.voicenr = None
        self.voicecontext = False
        self.piano_staff = -1
        self.sim_list = []
        self.seq_list = []
        self.new_context = None
        self.simsectnr = 0
        self.is_chord = False

    def parse_text(self, text, mode=None):
        state = ly.lex.state(mode) if mode else ly.lex.guessState(text)
        self.parse_tokens(state.tokens(text))

    def parse_tokens(self, tokens):
        for t in tokens:
            func_name = t.__class__.__name__ #get instance name
            if func_name != 'Space':
                try:
                    func_call = getattr(self, func_name)
                    func_call(t)
                except AttributeError:
                    # print "Warning: "+func_name+" not implemented!"
                    pass

    def musicxml(self, prettyprint=True):
        self.mediator.check_score()
        self.iterate_mediator()
        xml = self.musxml.musicxml(prettyprint)
        return xml

    ##
    # The different source types from ly.lex.lilypond are here sent to translation.
    ##

    def Name(self, token):
        """ name of variable """
        self.varname = token

    def SimultaneousStart(self, token):
        """ << """
        if self.new_context:
            self.sim_list.append(self.new_context)
            self.new_context = None
        else:
            if not self.simsectnr:
                self.curr_sect = self.mediator.insert_into
            self.simsectnr += 1
            self.varname = "sim-sect-"+str(self.simsectnr)
            self.can_create_sect = True

    def SimultaneousEnd(self, token):
        """ >> """
        if self.sim_list:
            if self.sim_list[-1] == 'pianostaff':
                if self.piano_var:
                    self.mediator.merge_variable(5, self.piano_var, True)
                    self.piano_var = None
            self.sim_list.pop()
        elif self.simsectnr:
            self.mediator.insert_into = self.curr_sect
            self.mediator.fetch_variable("sim-sect-1")
            self.mediator.new_bar()
            self.simsectnr = 0

    def SequentialStart(self, token):
        """ SequentialStart = { """
        if self.prev_command[1:] == 'times':
            self.tuplet = True
            self.ttype = "start"
        elif self.prev_command[1:] == 'grace':
            self.grace_seq = True
        elif self.prev_command == 'repeat':
            self.mediator.new_repeat('forward')
            self.prev_command = ''
            self.seq_list.append('repeat')
        elif self.new_context:
            self.seq_list.append(self.new_context)
            self.new_context = None
        elif self.can_create_sect:
            self.mediator.new_section(self.varname)
            self.can_create_sect = False
            self.varname = ''
            self.prev_command = ''
            self.seq_list.append("section")

    def SequentialEnd(self, token):
        """ SequentialEnd = } """
        if self.tuplet:
            self.mediator.change_to_tuplet(self.fraction, "stop")
            self.tuplet = False
        elif self.grace_seq:
            self.grace_seq = False
        elif self.simsectnr:
            if self.simsectnr>1:
                self.mediator.merge_variable(self.simsectnr,
                "sim-sect-"+str(self.simsectnr), False, "sim-sect-1")
            self.simsectnr += 1
            self.varname = "sim-sect-"+str(self.simsectnr)
            self.can_create_sect = True
            self.seq_list.pop()
        elif self.seq_list:
            if self.seq_list[-1] == 'pianostaff':
                if self.piano_var:
                    self.mediator.merge_variable(5, self.piano_var, True)
                    self.piano_var = None
            elif self.seq_list[-1] == 'section':
                self.can_create_sect = True
            elif self.seq_list[-1] == 'repeat':
                self.mediator.new_repeat('backward')
                self.mediator.new_bar()
            self.seq_list.pop()
        else:
            self.prev_command = ''

    def ChordStart(self, token):
        """ < """
        self.is_chord = True
        self.mediator.new_chord = True

    def ChordEnd(self, token):
        """ > """
        self.is_chord = False

    def Score(self, token):
        self.new_context = "score"

    def New(self, token):
        """ \new """
        self.new = True

    def Context(self, token):
        """ \context """
        self.context = True

    def ContextName(self, token):
        """ Staff, Voice  """
        if token == "Staff":
            if self.new or self.context:
                self.new_context = "staff"
            if self.new and "pianostaff" not in self.get_context():
                self.mediator.new_part()
                self.can_create_sect = False
                self.new = False
            elif self.piano_staff>=0:
                self.piano_staff += 1
        elif token == "PianoStaff":
            if self.new:
                self.mediator.new_part(True)
                self.new_context = "pianostaff"
                self.can_create_sect = False
                self.piano_staff = 0
                self.new = False
        elif token == "Voice":
            self.voicecontext = True
        else:
            print token
            self.new_context = token

    def ContextProperty(self, token):
        """ instrumentName, midiInstrument, etc """
        self.prev_command = token

    def get_context(self):
        curr_sim = ''
        curr_seq = ''
        if self.sim_list:
            curr_sim = self.sim_list[-1]
        if self.seq_list:
            curr_seq = self.seq_list[-1]
        return curr_sim, curr_seq

    def PipeSymbol(self, token):
        """ PipeSymbol = | """
        self.mediator.new_bar()

    def Clef(self, token):
        """ Clef \clef"""
        self.prev_command = "clef"

    def PitchCommand(self, token):
        if token == '\\relative':
            self.pitch_mode = 'rel'
            self.prev_command = token[1:]
        elif token == '\key':
            self.prev_command = "key"

    def Note(self, token):
        """ notename, e.g. c, cis, a bes ... """
        if self.prev_command == "key":
            self.key = token
        elif self.prev_command == "relative":
            self.mediator.set_relative(token)
        elif self.is_chord:
            self.mediator.create_chord(token, self.pitch_mode)
            self.mediator.new_chord = False
        else:
            self.mediator.new_note(token, self.pitch_mode)
            if self.tuplet:
                self.mediator.change_to_tuplet(self.fraction, self.ttype)
                self.ttype = ""
            if self.prev_command[1:] == 'grace':
                self.mediator.new_grace(0)
                if not self.grace_seq:
                    self.prev_command = ''

    def Octave(self, token):
        """ a number of , or ' """
        if self.prev_command == "relative":
            self.mediator.new_octave(token)
            self.prev_command = ''
        else:
            if self.pitch_mode == 'rel':
                self.mediator.new_octave(token, True)
            else:
                self.mediator.new_octave(token)

    def Length(self, token):
        """ note length/duration, e.g. 4, 8, 16 ... """
        self.duration = token
        self.mediator.new_duration(token)

    def TremoloDuration(self, token):
        """ duration of tremolo notes for tremolo marking """
        self.mediator.new_tremolo(token)

    def Dot(self, token):
        """ dot, . """
        self.mediator.new_dot()

    def Tie(self, token):
        """ tie ~ """
        self.mediator.tie_to_next()

    def Rest(self, token):
        """ rest, r or R. Note: NOT by command, i.e. \rest """
        if token == 'R':
            self.scale = token
        self.mediator.new_rest(token)

    def Spacer(self, token):
        """ invisible rest/spacer rest (s) """
        self.mediator.new_rest(token)

    def Skip(self, token):
        """ command \skip """
        self.mediator.new_rest('s')

    def Scaling(self, token):
        """ scaling, e.g. *3 or *2/3"""
        if self.scale == 'R':
            self.mediator.scale_rest(token[1:])
            self.scale = ''
        else:
            self.mediator.scale_duration(token)

    def Fraction(self, token):
        """ fraction, e.g. 3/4
        can be used for time sign or tuplets """
        if self.prev_command == '\\time':
            self.mediator.new_time(token)
            self.prev_command = ''
        elif self.prev_command == '\\numericTimeSignature':
            self.mediator.new_time(token, numeric=True)
            self.prev_command = ''
        else:
            self.fraction = token

    def Keyword(self, token):
        self.prev_command = token

    def Repeat(self, token):
        self.prev_command = "repeat"

    def Command(self, token):
        """ \bar, \rest, \time, etc """
        if token == '\\rest':
            self.mediator.note2rest()
        elif token.find('voice') == 1:
            self.voicenr = self.mediator.new_voice(token[1:])
        elif self.prev_command != '\\numericTimeSignature':
            self.prev_command = token

    def UserCommand(self, token):
        if self.prev_command == 'key':
            self.mediator.new_key(self.key, token)
            self.prev_command = ''
        else:
            if self.voicecontext and self.voicenr>1:
                if self.piano_staff == 2:
                    self.mediator.merge_variable(self.voicenr, token[1:], org=self.piano_var)
                else:
                    self.mediator.merge_variable(self.voicenr, token[1:])
            elif self.piano_staff == 2:
                self.piano_var = token[1:]
                self.piano_staff = -1
            else:
                self.mediator.fetch_variable(token[1:])

    def String(self, token):
        if self.prev_command == 'clef':
            self.mediator.new_clef(token)
            self.prev_command = ''
        elif self.prev_command == '\\bar':
            self.mediator.create_barline(token)
            self.prev_command = ''
        elif self.prev_command == 'instrumentName':
            self.mediator.set_partname(token)
            self.prev_command = ''


    ##
    # The xml-file is built from the mediator objects
    ##

    def iterate_mediator(self):
        """ the mediator lists are looped through and outputed to the xml-file """
        for part in self.mediator.score:
            if part.barlist:
                self.musxml.create_part(part.name)
                self.mediator.set_first_bar(part)
            else:
                print "Warning: empty part: "+part.name
            for bar in part.barlist:
                self.musxml.create_measure()
                for obj in bar:
                    if isinstance(obj, ly2xml_mediator.bar_attr):
                        if obj.has_attr():
                            self.musxml.new_bar_attr(obj.clef, obj.time, obj.key, obj.mode, obj.divs)
                        if obj.repeat:
                            self.musxml.add_barline(obj.barline, obj.repeat)
                        elif obj.barline:
                            self.musxml.add_barline(obj.barline)
                        if obj.staves:
                            self.musxml.add_staves(obj.staves)
                        if obj.multiclef:
                            for i, m in enumerate(obj.multiclef):
                                self.musxml.add_clef(m[0], m[1], i+1)
                    elif isinstance(obj, ly2xml_mediator.bar_note):
                        self.musxml.new_note(obj.grace, [obj.base_note, obj.pitch.alter, obj.pitch.octave], obj.duration,
                        obj.voice, obj.type, self.mediator.divisions, obj.dot, obj.chord)
                        if obj.tie:
                            self.musxml.tie_note(obj.tie)
                        if obj.tuplet:
                            self.musxml.tuplet_note(obj.tuplet, obj.duration, obj.ttype, self.mediator.divisions)
                        if obj.tremolo:
                            self.musxml.add_tremolo("single", obj.tremolo)
                        if obj.staff:
                            self.musxml.add_staff(obj.staff)
                    elif isinstance(obj, ly2xml_mediator.bar_rest):
                        if obj.skip:
                            self.musxml.new_skip(obj.duration, self.mediator.divisions)
                        else:
                            self.musxml.new_rest(obj.duration, obj.type, self.mediator.divisions, obj.pos, obj.dot, obj.voice)
                        if obj.staff and not obj.skip:
                            self.musxml.add_staff(obj.staff)
                    elif isinstance(obj, ly2xml_mediator.bar_backup):
                        self.musxml.new_backup(obj.duration, self.mediator.divisions)


