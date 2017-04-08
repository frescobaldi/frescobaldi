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
Percussion part types.
"""


from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QSpinBox)

import listmodel
import ly.dom

from . import _base
from . import register



class PitchedPercussionPart(_base.SingleVoicePart):
    """Base class for pitched percussion types."""


class Timpani(PitchedPercussionPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Timpani")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Timpani", "Tmp.")

    midiInstrument = 'timpani'
    clef = 'bass'
    octave = -1


class Xylophone(PitchedPercussionPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Xylophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Xylophone", "Xyl.")

    midiInstrument = 'xylophone'


class Marimba(_base.PianoStaffPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Marimba")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Marimba", "Mar.")

    midiInstrument = 'marimba'

    def createWidgets(self, layout):
        super(Marimba, self).createWidgets(layout)
        self.lowerVoices.setMinimum(0)

    def translateWidgets(self):
        self.upperVoicesLabel.setText(_("Upper staff:"))
        self.lowerVoicesLabel.setText(_("Lower staff:"))
        self.lowerVoices.setToolTip(_(
            "Set the number of voices to 0 to disable the second staff."))

    def build(self, data, builder):
        if self.lowerVoices.value():
            super(Marimba, self).build(data, builder)
        else:
            data.nodes.append(self.buildStaff(data, builder, None, 1))


class Vibraphone(Marimba):
    @staticmethod
    def title(_=_base.translate):
        return _("Vibraphone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Vibraphone", "Vib.")

    midiInstrument = 'vibraphone'


class TubularBells(PitchedPercussionPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Tubular bells")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Tubular bells", "Tub.")

    midiInstrument = 'tubular bells'


class Glockenspiel(PitchedPercussionPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Glockenspiel")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Glockenspiel", "Gls.")

    midiInstrument = 'glockenspiel'


class Carillon(_base.PianoStaffPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Carillon")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Carillon", "Car.")

    midiInstrument = 'tubular bells' # anyone knows better?

    def translateWidgets(self):
        super(Carillon, self).translateWidgets()
        self.upperVoicesLabel.setText(_("Manual staff:"))
        self.lowerVoicesLabel.setText(_("Pedal staff:"))

    def build(self, data, builder):
        p = ly.dom.PianoStaff()
        builder.setInstrumentNamesFromPart(p, self, data)
        s = ly.dom.Sim(p)
        # add two staves, with a respective number of voices.
        self.buildStaff(data, builder, 'manual', 1, self.upperVoices.value(), s)
        self.buildStaff(data, builder, 'pedal', 0, self.lowerVoices.value(), s, "bass")
        data.nodes.append(p)


class Drums(_base.Part):
    @staticmethod
    def title(_=_base.translate):
        return _("Drums")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Drums", "Dr.")

    def createWidgets(self, layout):
        self.voicesLabel = QLabel()
        self.voices = QSpinBox(minimum=1, maximum=4, value=1)
        self.drumStyleLabel = QLabel()
        self.drumStyle = QComboBox()
        self.drumStyle.setModel(listmodel.ListModel(drumStyles, self.drumStyle, display=listmodel.translate))
        self.drumStems = QCheckBox()

        box = QHBoxLayout()
        box.addWidget(self.voicesLabel)
        box.addWidget(self.voices)
        layout.addLayout(box)
        box = QHBoxLayout()
        box.addWidget(self.drumStyleLabel)
        box.addWidget(self.drumStyle)
        layout.addLayout(box)
        layout.addWidget(self.drumStems)

    def translateWidgets(self):
        self.voicesLabel.setText(_("Voices:"))
        self.drumStyleLabel.setText(_("Style:"))
        self.drumStems.setText(_("Remove stems"))
        self.drumStems.setToolTip(_("Remove the stems from the drum notes."))
        self.drumStyle.model().update()

    def assignDrums(self, data, name = None):
        r"""Creates an empty name = \drummode assignment.

        Returns the assignment.

        """
        a = data.assign(name)
        s = ly.dom.DrumMode(a)
        ly.dom.Identifier(data.globalName, s)
        ly.dom.LineComment(_("Drums follow here."), s)
        ly.dom.BlankLine(s)
        return a

    def build(self, data, builder):
        p = ly.dom.DrumStaff()
        s = ly.dom.Simr(p)
        if self.voices.value() > 1:
            for i in range(1, self.voices.value() + 1):
                q = ly.dom.Seq(ly.dom.DrumVoice(parent=s))
                ly.dom.Text('\\voice' + ly.util.int2text(i), q)
                a = self.assignDrums(data, 'drum' + ly.util.int2text(i))
                ly.dom.Identifier(a.name, q)
        else:
            a = self.assignDrums(data, 'drum')
            ly.dom.Identifier(a.name, s)
        builder.setInstrumentNamesFromPart(p, self, data)
        i = self.drumStyle.currentIndex()
        if i > 0:
            v = ('drums', 'timbales', 'congas', 'bongos', 'percussion')[i]
            p.getWith()['drumStyleTable'] = ly.dom.Scheme(v + '-style')
            v = (5, 2, 2, 2, 1)[i]
            ly.dom.Line("\\override StaffSymbol #'line-count = #{0}".format(v), p.getWith())
        if self.drumStems.isChecked():
            ly.dom.Line("\\override Stem #'stencil = ##f", p.getWith())
            ly.dom.Line("\\override Stem #'length = #3  % " + _("keep some distance."),
                p.getWith())
        data.nodes.append(p)


drumStyles = (
    lambda: _("Drums (5 lines, default)"),
    lambda: _("Timbales-style (2 lines)"),
    lambda: _("Congas-style (2 lines)"),
    lambda: _("Bongos-style (2 lines)"),
    lambda: _("Percussion-style (1 line)"),
)



register(
    lambda: _("Percussion"),
    [
        Timpani,
        Xylophone,
        Marimba,
        Vibraphone,
        TubularBells,
        Glockenspiel,
        Carillon,
        Drums,
    ])
