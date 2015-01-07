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
The xml-file is built from the mediator objects

"""

from __future__ import unicode_literals
from __future__ import print_function

from . import xml_objs


class iterateMediatorScore():

    def __init__(self, score, musxml, div):
        """ The mediator score is looped through and outputed to the xml-file. """
        # score.debug_score([])
        self.musxml = musxml
        self.divisions = div
        if score.title:
            self.musxml.create_title(score.title)
        for ctag in score.creators:
            self.musxml.add_creator(ctag, score.creators[ctag])
        for itag in score.info:
            self.musxml.create_score_info(itag, score.info[itag])
        if score.rights:
            self.musxml.add_rights(score.rights)
        for p in score.partlist:
            if isinstance(p, xml_objs.ScorePart):
                self.iterate_part(p)
            elif isinstance(p, xml_objs.ScorePartGroup):
                self.iterate_partgroup(p)

    def iterate_partgroup(self, group):
        """Loop through a group, recursively if nested."""
        self.musxml.create_partgroup(
            'start', group.num, group.name, group.abbr, group.bracket)
        for p in group.partlist:
            if isinstance(p, xml_objs.ScorePart):
                self.iterate_part(p)
            elif isinstance(p, xml_objs.ScorePartGroup):
                self.iterate_partgroup(p)
        self.musxml.create_partgroup('stop', group.num)

    def iterate_part(self, part):
        """The part is iterated."""
        if part.barlist:
            part.set_first_bar(self.divisions)
            self.musxml.create_part(part.name, part.abbr, part.midi)
            for bar in part.barlist:
                self.iterate_bar(bar)
        else:
            print("Warning: empty part:", part.name)

    def iterate_bar(self, bar):
        """The objects in the bar is outputed to the xml-file."""
        self.musxml.create_measure()
        for obj in bar.obj_list:
            if isinstance(obj, xml_objs.BarAttr):
                self.new_xml_bar_attr(obj)
            elif isinstance(obj, xml_objs.BarMus):
                self.before_note(obj)
                if isinstance(obj, xml_objs.BarNote):
                    self.new_xml_note(obj)
                elif isinstance(obj, xml_objs.BarRest):
                    self.new_xml_rest(obj)
                self.gener_xml_mus(obj)
                self.after_note(obj)
            elif isinstance(obj, xml_objs.BarBackup):
                self.musxml.new_backup(obj.duration, self.divisions)

    def new_xml_bar_attr(self, obj):
        """Create bar attribute xml-nodes."""
        if obj.has_attr():
            self.musxml.new_bar_attr(obj.clef, obj.time, obj.key, obj.mode, obj.divs)
        if obj.repeat:
            self.musxml.add_barline(obj.barline, obj.repeat)
        elif obj.barline:
            self.musxml.add_barline(obj.barline)
        if obj.staves:
            self.musxml.add_staves(obj.staves)
        if obj.multiclef:
            for mc in obj.multiclef:
                self.musxml.add_clef(sign=mc[0][0], line=mc[0][1], nr=mc[1], oct_ch=mc[0][2])
        if obj.tempo:
            self.musxml.create_tempo(obj.tempo.metr, obj.tempo.midi, obj.tempo.dots)

    def before_note(self, obj):
        """Xml-nodes before note."""
        if obj.dynamic['before']:
            if obj.dynamic['before']['mark']:
                self.musxml.add_dynamic_mark(obj.dynamic['before']['mark'])
            if obj.dynamic['before']['wedge']:
                self.musxml.add_dynamic_wedge(obj.dynamic['before']['wedge'])

    def after_note(self, obj):
        """Xml-nodes after note."""
        if obj.dynamic['after']:
            if obj.dynamic['after']['mark']:
                self.musxml.add_dynamic_mark(obj.dynamic['after']['mark'])
            if obj.dynamic['after']['wedge']:
                self.musxml.add_dynamic_wedge(obj.dynamic['after']['wedge'])
        if obj.oct_shift:
            self.musxml.add_octave_shift(obj.oct_shift.plac, obj.oct_shift.octdir, obj.oct_shift.size)

    def gener_xml_mus(self, obj):
        """Nodes generic for both notes and rests."""
        if obj.tuplet:
            self.musxml.tuplet_note(obj.tuplet, obj.duration, obj.ttype, self.divisions)
        if obj.staff and not obj.skip:
            self.musxml.add_staff(obj.staff)
        if obj.other_notation:
            self.musxml.add_named_notation(obj.other_notation)

    def new_xml_note(self, obj):
        """Create note specific xml-nodes."""
        self.musxml.new_note(obj.grace, [obj.base_note, obj.alter, obj.octave,
            obj.accidental_token], obj.duration, obj.voice, obj.type,
            self.divisions, obj.dot, obj.chord)
        for t in obj.tie:
            self.musxml.tie_note(t)
        for s in obj.slur:
            self.musxml.add_slur(1, s) #LilyPond doesn't allow nested slurs so the number can be 1
        for a in obj.artic:
            self.musxml.new_articulation(a)
        if obj.ornament:
            self.musxml.new_simple_ornament(obj.ornament)
        if obj.adv_ornament:
            self.musxml.new_adv_ornament(obj.adv_ornament[0], obj.adv_ornament[1])
        if obj.tremolo[1]:
            self.musxml.add_tremolo(obj.tremolo[0], obj.tremolo[1])
        if obj.gliss:
            self.musxml.add_gliss(obj.gliss[0], obj.gliss[1], obj.gliss[2])
        if obj.fingering:
            self.musxml.add_fingering(obj.fingering)
        if obj.lyric:
            for l in obj.lyric:
                try:
                   self.musxml.add_lyric(l[0], l[1], l[2], l[3])
                except IndexError:
                    self.musxml.add_lyric(l[0], l[1], l[2])

    def new_xml_rest(self, obj):
        """Create rest specific xml-nodes."""
        if obj.skip:
            self.musxml.new_skip(obj.duration, self.divisions)
        else:
            self.musxml.new_rest(obj.duration, obj.type, self.divisions, obj.pos,
            obj.dot, obj.voice)
