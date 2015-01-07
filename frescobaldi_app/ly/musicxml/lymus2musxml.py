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
from __future__ import print_function

import documentinfo
import ly.music

from . import create_musicxml
from . import iter_mediator
from . import ly2xml_mediator

#excluded from parsing
excl_list = ['Version', 'Midi', 'Layout']


# Defining contexts in relation to musicXML
group_contexts = ['StaffGroup', 'ChoirStaff']

pno_contexts = ['PianoStaff', 'GrandStaff']

staff_contexts = ['Staff', 'RhythmicStaff', 'TabStaff',
    'DrumStaff', 'VaticanaStaff', 'MensuralStaff']

part_contexts = pno_contexts + staff_contexts


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
        self.piano_staff = 0
        self.numericTime = False
        self.voice_sep = False
        self.sims_and_seqs = []
        self.override_dict = {}
        self.ottava = False
        self.with_contxt = None
        self.schm_assignm = None

    def parse_tree(self, doc):
        mustree = documentinfo.music(doc)
        # print(mustree.dump())
        header_nodes = self.iter_header(mustree)
        if header_nodes:
            self.parse_nodes(header_nodes)
        score = self.get_score(mustree)
        if score:
            mus_nodes = self.iter_score(score, mustree)
        else:
            mus_nodes = self.find_score_sub(mustree)
        self.mediator.new_section("fallback") #fallback/default section
        self.parse_nodes(mus_nodes)

    def parse_nodes(self, nodes):
        """Work through all nodes by calling the function with the
        same name as the nodes class."""
        if nodes:
            for m in nodes:
                # print(m)
                func_name = m.__class__.__name__ #get instance name
                if func_name not in excl_list:
                    try:
                        func_call = getattr(self, func_name)
                        func_call(m)
                    except AttributeError as ae:
                        print("Warning:", func_name, "not implemented!")
                        print(ae)
                        pass
        else:
            print("Warning! Couldn't parse source!")

    def musicxml(self, prettyprint=True):
        self.mediator.check_score()
        iter_mediator.iterateMediatorScore(
            self.mediator.score, self.musxml, self.mediator.divisions)
        xml = self.musxml.musicxml(prettyprint)
        return xml

    ##
    # The different source types from ly.music are here sent to translation.
    ##

    def Assignment(self, a):
        """
        Variables should already have been substituted
        so this need only cover other types of assignments.
        """
        if isinstance(a.value(), ly.music.items.Markup):
            val = a.value().plaintext()
        elif isinstance(a.value(), ly.music.items.String):
            val = a.value().value()
        elif isinstance(a.value(), ly.music.items.Scheme):
            val = a.value().get_string()
            if not val:
                self.schm_assignm = a.name()
        if self.look_behind(a, ly.music.items.With):
            if self.with_contxt in group_contexts:
                self.mediator.set_by_property(a.name(), val, True)
            else:
                self.mediator.set_by_property(a.name(), val)
        else:
            self.mediator.new_header_assignment(a.name(), val)

    def MusicList(self, musicList):
        if musicList.token == '<<':
            if self.look_ahead(musicList, ly.music.items.VoiceSeparator):
                self.mediator.new_snippet('sim-snip')
                self.voice_sep = True
            else:
                self.sims_and_seqs.append('sim')
        elif musicList.token == '{':
            if self.sims_and_seqs and self.sims_and_seqs[-1] == 'sim':
                self.mediator.new_section('simultan')
            self.sims_and_seqs.append('seq')
            # print(self.sims_and_seqs)

    def Chord(self, chord):
        self.mediator.clear_chord()

    def Q(self, q):
        self.mediator.copy_prev_chord(q.duration)

    def Context(self, context):
        """ \context """
        self.in_context = True
        if context.context() in pno_contexts:
            self.mediator.new_part(piano=True)
            self.piano_staff = 1
        elif context.context() in group_contexts:
            self.mediator.new_group()
        elif context.context() in staff_contexts:
            if self.piano_staff:
                if self.piano_staff > 1:
                    self.mediator.set_voicenr(nr=self.piano_staff+3)
                self.mediator.new_section('piano-staff'+str(self.piano_staff))
                self.mediator.set_staffnr(self.piano_staff)
                self.piano_staff += 1
            else:
                # Check first if part already exists
                if context.token != '\\context' or self.mediator.part_not_empty():
                    self.mediator.new_part()
            self.mediator.add_staff_id(context.context_id())
        elif context.context() == 'Voice':
            self.sims_and_seqs.append('voice')
            if context.context_id():
                self.mediator.new_section(context.context_id())
            else:
                self.mediator.new_section('voice')
        else:
            print("Context not implemented:", context.context())

    def VoiceSeparator(self, voice_sep):
        self.mediator.new_snippet('sim')
        self.mediator.set_voicenr(add=True)

    def Change(self, change):
        """ A \\change music expression. Changes the staff number. """
        if change.context() == 'Staff':
            self.mediator.set_staffnr(0, staff_id=change.context_id())

    def PipeSymbol(self, barcheck):
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
        #print(note.token)
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
                self.mediator.set_relative(note)
                self.relative = True
            elif isinstance(note.parent(), ly.music.items.Chord):
                self.mediator.new_chord(note, note.parent().duration, self.relative)
                # chord as grace note
                if self.grace_seq:
                    self.mediator.new_chord_grace()

    def Duration(self, duration):
        """A written duration"""
        self.mediator.new_duration_token(duration.token, duration.tokens)

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
        if 'lyrics' in self.sims_and_seqs:
            self.mediator.new_lyrics_item(skip.token)
        else:
            self.mediator.new_rest(skip)

    def Scaler(self, scaler):
        """
        \times \tuplet \scaleDurations

        """
        if scaler.token == '\\scaleDurations':
            self.ttype = ""
            self.fraction = (scaler.denominator, scaler.numerator)
        elif scaler.token == '\\times':
            self.ttype = "start"
            self.fraction = (scaler.denominator, scaler.numerator)
        elif scaler.token == '\\tuplet':
            self.ttype = "start"
            self.fraction = (scaler.numerator, scaler.denominator)
        self.tuplet = True

    def Number(self, number):
        pass

    def Articulation(self, art):
        """An articulation, fingering, string number, or other symbol."""
        self.mediator.new_articulation(art.token)

    def Postfix(self, postfix):
        pass

    def Beam(self, beam):
        pass

    def Slur(self, slur):
        """ Slur, '(' = start, ')' = stop. """
        if slur.token == '(':
            self.mediator.set_slur("start")
        elif slur.token == ')':
            self.mediator.set_slur("stop")

    def Dynamic(self, dynamic):
        """Any dynamic symbol."""
        self.mediator.new_dynamics(dynamic.token[1:])

    def Grace(self, grace):
        self.grace_seq = True

    def TimeSignature(self, timeSign):
        self.mediator.new_time(timeSign.numerator(), timeSign.fraction(), self.numericTime)

    def Repeat(self, repeat):
        if repeat.specifier() == 'volta':
            self.mediator.new_repeat('forward')
        elif repeat.specifier() == 'tremolo':
            self.trem_rep = repeat.repeat_count()

    def Tremolo(self, tremolo):
        self.mediator.set_tremolo(duration=int(tremolo.duration.token))

    def With(self, cont_with):
        """A \\with ... construct."""
        self.with_contxt = cont_with.parent().context()

    def Set(self, cont_set):
        """A \\set command."""
        if isinstance(cont_set.value(), ly.music.items.Scheme):
            val = cont_set.value().get_string()
        else:
            val = cont_set.value().value()
        if cont_set.context() in part_contexts:
            self.mediator.set_by_property(cont_set.property(), val)
        elif cont_set.context() in group_contexts:
            self.mediator.set_by_property(cont_set.property(), val, group=True)

    def Command(self, command):
        """ \bar, \rest etc """
        if command.token == '\\rest':
            self.mediator.note2rest()
        elif command.token == '\\numericTimeSignature':
            self.numericTime = True
        elif command.token == '\\defaultTimeSignature':
            self.numericTime = False
        elif command.token.find('voice') == 1:
            self.mediator.set_voicenr(command.token[1:], piano=self.piano_staff)
        elif command.token == '\\glissando':
            try:
                self.mediator.new_gliss(self.override_dict["Glissando.style"])
            except KeyError:
                self.mediator.new_gliss()
        elif command.token == '\\startTrillSpan':
            self.mediator.new_trill_spanner()
        elif command.token == '\\stopTrillSpan':
            self.mediator.new_trill_spanner("stop")
        elif command.token == '\\ottava':
            self.ottava = True
        else:
            print("Unknown command:", command.token)

    def String(self, string):
        prev = self.get_previous_node(string)
        if prev and prev.token == '\\bar':
            self.mediator.create_barline(string.value())

    def LyricsTo(self, lyrics_to):
        """A \\lyricsto expression. """
        self.mediator.new_lyric_section('lyricsto'+lyrics_to.context_id(), lyrics_to.context_id())
        self.sims_and_seqs.append('lyrics')

    def LyricText(self, lyrics_text):
        """A lyric text (word, markup or string), with a Duration."""
        self.mediator.new_lyrics_text(lyrics_text.token)

    def LyricItem(self, lyrics_item):
        """Another lyric item (skip, extender, hyphen or tie)."""
        self.mediator.new_lyrics_item(lyrics_item.token)

    def LyricMode(self, lyric_mode):
        """A \\lyricmode, \\lyrics or \\addlyrics expression."""
        pass

    def Override(self, override):
        """An \\override command."""
        self.override_key = ''

    def PathItem(self, item):
        """An item in the path of an \\override or \\revert command."""
        self.override_key += item.token

    def Scheme(self, scheme):
        """A Scheme expression inside LilyPond."""
        pass

    def SchemeItem(self, item):
        """Any scheme token."""
        if self.ottava:
            self.mediator.new_ottava(item.token)
        elif self.look_behind(item, ly.music.items.Override):
            self.override_dict[self.override_key] = item.token
        elif self.schm_assignm:
            self.mediator.set_by_property(self.schm_assignm, item.token)
        else:
            print("SchemeItem not implemented:", item.token)

    def SchemeQuote(self, quote):
        """A ' in scheme."""
        pass

    def End(self, end):
        if isinstance(end.node, ly.music.items.Scaler):
            if end.node.token == '\scaleDurations':
                self.mediator.change_to_tuplet(self.fraction, "")
            else:
                self.mediator.change_to_tuplet(self.fraction, "stop")
            self.tuplet = False
            self.fraction = None
        elif isinstance(end.node, ly.music.items.Grace): #Grace
            self.grace_seq = False
        elif end.node.token == '\\repeat':
            if end.node.specifier() == 'volta':
                self.mediator.new_repeat('backward')
            elif end.node.specifier() == 'tremolo':
                if self.look_ahead(end.node, ly.music.items.MusicList):
                    self.mediator.set_tremolo(trem_type="stop", repeats=self.trem_rep)
                else:
                    self.mediator.set_tremolo(trem_type="single", repeats=self.trem_rep)
                self.trem_rep = 0
        elif isinstance(end.node, ly.music.items.Context):
            self.in_context = False
            if end.node.context() == 'Voice':
                self.mediator.check_voices()
                self.sims_and_seqs.pop()
            elif end.node.context() in group_contexts:
                self.mediator.close_group()
            elif end.node.context() in staff_contexts:
                if not self.piano_staff:
                    self.mediator.check_part()
            elif end.node.context() in pno_contexts:
                self.mediator.check_voices()
                self.mediator.check_part()
                self.piano_staff = 0
                self.mediator.set_voicenr(nr=1)
        elif end.node.token == '<<':
            if self.voice_sep:
                self.mediator.check_voices_by_nr()
                self.mediator.revert_voicenr()
                self.voice_sep = False
            elif not self.piano_staff:
                self.mediator.check_voices()
                self.mediator.check_part()
                if self.sims_and_seqs:
                    self.sims_and_seqs.pop()
        elif end.node.token == '{':
            if self.sims_and_seqs:
                self.sims_and_seqs.pop()
        elif end.node.token == '<': #chord
            self.mediator.chord_end()
        elif end.node.token == '\\lyricsto':
            self.mediator.check_lyrics(end.node.context_id())
            self.sims_and_seqs.pop()
        elif end.node.token == '\\with':
            self.with_contxt = None
        else:
            # print("end:", end.node.token)
            pass

    ##
    # Additional node manipulation
    ##

    def get_previous_node(self, node):
        """ Returns the nodes previous node
        or false if the node is first in its branch. """
        parent = node.parent()
        i = parent.index(node)
        if i > 0:
            return parent[i-1]
        else:
            return False

    def simple_node_gen(self, node):
        """Unlike iter_score are the subnodes yielded without substitution."""
        for n in node:
            yield n
            for s in self.simple_node_gen(n):
                yield s

    def iter_header(self, tree):
        """Iter only over header nodes."""
        for t in tree:
            if isinstance(t, ly.music.items.Header):
                return self.simple_node_gen(t)

    def get_score(self, node):
        """ Returns (first) Score node or false if no Score is found. """
        for n in node:
            if isinstance(n, ly.music.items.Score) or isinstance(n, ly.music.items.Book):
                return n
        return False

    def iter_score(self, scorenode, doc):
        """
        Iter over score.

        Similarly to items.Document.iter_music user commands are substituted.

        Furthermore \\repeat unfold expressions are unfolded.
        """
        for s in scorenode:
            if isinstance(s, ly.music.items.Repeat) and s.specifier() == 'unfold':
                for u in self.unfold_repeat(s, s.repeat_count(), doc):
                    yield u
            else:
                n = doc.substitute_for_node(s) or s
                yield n
                for c in self.iter_score(n, doc):
                    yield c
        if isinstance(scorenode, ly.music.items.Container):
            yield End(scorenode)

    def unfold_repeat(self, repeat_node, repeat_count, doc):
        """
        Iter over node which represent a \\repeat unfold expression
        and do the unfolding directly.
        """
        for r in range(repeat_count):
            for n in repeat_node:
                for c in self.iter_score(n, doc):
                    yield c

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

    def look_behind(self, node, find_node):
        """Looks behind on the parent node(s) and returns True
        if the search is successful."""
        parent = node.parent()
        if parent:
            if isinstance(parent, find_node):
                ret = True
            else:
                ret = self.look_behind(parent, find_node)
            return ret
        else:
            return False

    ##
    # Other functions
    ##
    def gen_med_caller(self, func_name, *args):
        """Call any function in the mediator object."""
        func_call = getattr(self.mediator, func_name)
        func_call(*args)

