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
Export to Music XML.

Using ly.music document tree to convert the source to XML.

Uses functions similar to items.Document.iter_music() to iter through
the node tree. But information about where a node branch ends
is also added.

This approach substitues the previous method of using ly.lex directly
to parse the source. It should prove more stable and easier to implement.

"""

from __future__ import unicode_literals

import documentinfo
import ly.music

from . import create_musicxml
from . import ly2xml_mediator

#excluded from parsing
excl_list = ['Version', 'Midi', 'Layout']


class End():
    """ Extra class that gives information about the end of Container
    elements in the node list. """
    def __init__(self, node):
        self.node = node


class ParseSource():
    """ creates the XML-file from the source code according to the Music XML standard """

    def __init__(self):
        self.musxml = create_musicxml.CreateMusicXML()
        self.mediator = ly2xml_mediator.Mediator()
        self.relative = False
        self.tuplet = False
        self.scale = ''
        self.grace_seq = False
        self.trem_rep = 0
        self.voicenr = None
        self.piano_staff = 0
        self.numericTime = False
        self.voice_sep = False

    def parse_tree(self, doc):
        mustree = documentinfo.music(doc)
        print(mustree.dump())
        score = self.get_score(mustree)
        if score:
            mus_nodes = self.iter_score(score, mustree)
        else:
            mus_nodes = self.find_score_sub(mustree)
        self.mediator.new_section("fallback") #fallback section
        if mus_nodes:
            for m in mus_nodes:
                func_name = m.__class__.__name__ #get instance name
                #print func_name
                if func_name not in excl_list:
                    try:
                        func_call = getattr(self, func_name)
                        func_call(m)
                    except AttributeError as ae:
                        print "Warning: "+func_name+" not implemented!"
                        print(ae)
                        pass
        else:
            print("Warning! Couldn't parse source!")

    def musicxml(self, prettyprint=True):
        self.mediator.check_score()
        self.iterate_mediator()
        xml = self.musxml.musicxml(prettyprint)
        return xml

    ##
    # The different source types from ly.music are here sent to translation.
    ##

    def Assignment(self, assignm):
        print("Warning assignment in score block or corresponding: "+assignm.name())

    def MusicList(self, musicList):
        if musicList.token == '<<':
            if self.look_ahead(musicList, ly.music.items.VoiceSeparator):
                self.mediator.new_snippet('sim')
                self.voice_sep = True

    def Chord(self, chord):
        self.mediator.clear_chord()

    def Q(self, q):
        self.mediator.copy_prev_chord(q.duration, self.relative)

    def Context(self, context):
        """ \context """
        if context.context() in ['PianoStaff', 'GrandStaff']:
            self.mediator.new_part(piano=True)
            self.piano_staff = 1
        elif context.context() == 'Staff':
            if self.piano_staff:
                if self.piano_staff > 1:
                    self.mediator.set_voicenr(nr=self.piano_staff+3)
                self.mediator.new_section('piano-staff'+str(self.piano_staff))
                self.mediator.set_staffnr(self.piano_staff)
                self.piano_staff += 1
            else:
                self.mediator.new_part()
        elif context.context() == 'Voice':
            if context.context_id():
                self.mediator.new_section(context.context_id())
            else:
                self.mediator.new_section('voice')

    def VoiceSeparator(self, voice_sep):
        self.mediator.new_snippet('sim')
        self.mediator.set_voicenr(add=True)

    def PipeSymbol(self,barcheck):
        """ PipeSymbol = | """
        self.mediator.new_bar()

    def Clef(self, clef):
        """ Clef \clef"""
        self.mediator.new_clef(clef.specifier())

    def KeySignature(self, key):
        self.mediator.new_key(key.pitch().output(), key.mode())

    def Relative(self, relative):
        pass

    def Note(self, note):
        """ notename, e.g. c, cis, a bes ... """
        print(note.token)
        if note.length():
            self.mediator.new_note(note, self.relative)
            if self.tuplet:
                self.mediator.change_to_tuplet(self.fraction, self.ttype)
                self.ttype = ""
            if self.grace_seq:
                self.mediator.new_grace()
            if self.trem_rep:
                self.mediator.set_tremolo(trem_type='start', repeats=self.trem_rep)
        else:
            if isinstance(note.parent(), ly.music.items.Relative):
                print("setting relative")
                self.mediator.set_relative(note)
                self.relative = True
            elif isinstance(note.parent(), ly.music.items.Chord):
                self.mediator.new_chord(note, note.parent().duration, self.relative)

    def Tempo(self, tempo):
        """ Tempo direction, e g '4 = 80' """
        self.mediator.new_tempo(tempo.duration.tokens, tempo.tempo(), tempo.text())

    def Tie(self, tie):
        """ tie ~ """
        self.mediator.tie_to_next()

    def Rest(self, rest):
        """ rest, r or R. Note: NOT by command, i.e. \rest """
        if rest.token == 'R':
            self.scale = 'R'
        self.mediator.new_rest(rest)

    def Skip(self, skip):
        """ invisible rest/spacer rest (s or command \skip)"""
        self.mediator.new_rest(skip)

    def Scaler(self, scaler):
        """ \times \tuplet \scaleDurations"""
        if not scaler.token == '\\scaleDurations': #I'll come back for this later
            self.tuplet = True
            self.ttype = "start"
            self.fraction = scaler.scaling

    def Grace(self, grace):
        self.grace_seq = True

    def TimeSignature(self, timeSign):
        self.mediator.new_time(timeSign.numerator(), timeSign.fraction(), self.numericTime)

    def Repeat(self, repeat):
        if repeat.specifier() == 'volta':
            self.mediator.new_repeat('forward')
        elif repeat.specifier() == 'unfold':
            self.mediator.new_snippet('unfold')
        elif repeat.specifier() == 'tremolo':
            self.trem_rep = repeat.repeat_count()

    def Tremolo(self, tremolo):
        self.mediator.set_tremolo(duration=int(tremolo.duration.token))

    def With(self, cont_with):
        print(cont_with.tokens)

    def Set(self, cont_set):
        if cont_set.property() == 'instrumentName':
            self.mediator.set_partname(cont_set.value().value())
        elif cont_set.property() == 'midiInstrument':
            self.mediator.set_partmidi(cont_set.value().value())

    def Command(self, command):
        """ \bar, \rest etc """
        print(command.token)
        if command.token == '\\rest':
            self.mediator.note2rest()
        elif command.token == '\\numericTimeSignature':
            self.numericTime = True
        elif command.token == '\\defaultTimeSignature':
            self.numericTime = False
        elif command.token.find('voice') == 1:
            self.voicenr = self.mediator.set_voicenr(command.token[1:], piano=self.piano_staff)

    def String(self, string):
        prev = self.get_previous_node(string)
        if prev and prev.token == '\\bar':
            self.mediator.create_barline(string.value())

    def End(self, end):
        if isinstance(end.node, ly.music.items.Scaler):
            if not end.node.token == '\scaleDurations':
                self.mediator.change_to_tuplet(self.fraction, "stop")
                self.tuplet = False
                self.fraction = None
        elif isinstance(end.node, ly.music.items.Grace): #Grace
            self.grace_seq = False
        elif end.node.token == '\\repeat':
            if end.node.specifier() == 'volta':
                self.mediator.new_repeat('backward')
            elif end.node.specifier() == 'unfold':
                for n in range(end.node.repeat_count()):
                    self.mediator.add_snippet('unfold')
            elif end.node.specifier() == 'tremolo':
                if self.look_ahead(end.node, ly.music.items.MusicList):
                    self.mediator.set_tremolo(trem_type="stop", repeats=self.trem_rep)
                else:
                    self.mediator.set_tremolo(trem_type="single", repeats=self.trem_rep)
                self.trem_rep = 0
        elif isinstance(end.node, ly.music.items.Context):
            if end.node.context() == 'Voice':
                self.mediator.check_voices()
            elif end.node.context() == 'Staff':
                if not self.piano_staff:
                    self.mediator.check_part()
            elif end.node.context() in ['PianoStaff', 'GrandStaff']:
                self.mediator.check_voices()
                self.mediator.check_part()
                self.piano_staff = 0
                self.mediator.set_voicenr(nr=1)
        elif end.node.token == '<<':
            if self.voice_sep:
                self.mediator.check_voices_by_nr()
                self.mediator.revert_voicenr()
                self.voice_sep = False
        else:
            print("end:"+end.node.token)

    ##
    # Additional node manipulation
    ##

    def get_previous_node(self, node):
        """ returns the nodes previous node
        or false if the node is first """
        parent = node.parent()
        i = parent.index(node)
        if i > 0:
            return parent[i-1]
        else:
            return False

    def get_score(self, node):
        """ returns (first) Score node or false if no Score is found """
        for n in node:
            if isinstance(n, ly.music.items.Score) or isinstance(n, ly.music.items.Book):
                return n
        return False

    def iter_score(self, scorenode, doc):
        """Iter over score. Similar to items.Document.iter_music."""
        for s in scorenode:
            n = doc.substitute_for_node(s) or s
            yield n
            for n in self.iter_score(n, doc):
                yield n
        if isinstance(scorenode, ly.music.items.Container):
            yield End(scorenode)

    def find_score_sub(self, doc):
        """Find substitute for scorenode. Takes first music node that isn't
        an assignment."""
        for n in doc:
            if not isinstance(n, ly.music.items.Assignment):
                if isinstance(n, ly.music.items.Music):
                    return self.iter_score(n, doc)

    def look_ahead(self, node, find_node):
        """Looks ahead in a container node and returns True
        if the search is successful."""
        for n in node:
            if isinstance(n, find_node):
                return True
        return False

    ##
    # The xml-file is built from the mediator objects
    ##

    def iterate_mediator(self):
        """ the mediator lists are looped through and outputed to the xml-file """
        for part in self.mediator.score:
            if part.barlist:
                self.musxml.create_part(part.name, part.midi)
                self.mediator.set_first_bar(part)
            else:
                print "Warning: empty part: "+part.name
            for bar in part.barlist:
                self.musxml.create_measure()
                for obj in bar.obj_list:
                    if isinstance(obj, ly2xml_mediator.BarAttr):
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
                        if obj.tempo:
                            self.musxml.create_tempo(obj.tempo.metr, obj.tempo.midi, obj.tempo.dots)
                    elif isinstance(obj, ly2xml_mediator.BarNote):
                        self.musxml.new_note(obj.grace, [obj.base_note, obj.alter, obj.pitch.octave], obj.base_scaling,
                        obj.voice, obj.type, self.mediator.divisions, obj.dot, obj.chord)
                        if obj.tie:
                            self.musxml.tie_note(obj.tie)
                        if obj.tuplet:
                            self.musxml.tuplet_note(obj.tuplet, obj.base_scaling, obj.ttype, self.mediator.divisions)
                        if obj.tremolo[1]:
                            self.musxml.add_tremolo(obj.tremolo[0], obj.tremolo[1])
                        if obj.staff:
                            self.musxml.add_staff(obj.staff)
                    elif isinstance(obj, ly2xml_mediator.BarRest):
                        if obj.skip:
                            self.musxml.new_skip(obj.base_scaling, self.mediator.divisions)
                        else:
                            self.musxml.new_rest(obj.base_scaling, obj.type, self.mediator.divisions, obj.pos, obj.dot, obj.voice)
                        if obj.staff and not obj.skip:
                            self.musxml.add_staff(obj.staff)
                    elif isinstance(obj, ly2xml_mediator.BarBackup):
                        self.musxml.new_backup(obj.base_scaling, self.mediator.divisions)


