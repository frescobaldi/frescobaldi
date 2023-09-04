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
Keyboard part types.
"""


from PyQt5.QtWidgets import QGridLayout, QLabel, QSpinBox

import ly.dom
import ly.util

from . import _base
from . import register


class KeyboardPart(_base.PianoStaffPart):
    pass


class Piano(KeyboardPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Piano")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Piano", "Pno.")

    midiInstrument = 'acoustic grand'
    midiInstruments = (
        'acoustic grand',
        'bright acoustic',
        'electric grand',
        'honky-tonk',
    )


class ElectricPiano(KeyboardPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Electric piano")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Electric piano", "E.Pno.")

    midiInstrument = 'electric piano 1'
    midiInstruments = (
        'electric piano 1',
        'electric piano 2',
    )


class Harpsichord(KeyboardPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Harpsichord")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Harpsichord", "Hs.")

    midiInstrument = 'harpsichord'


class Clavichord(KeyboardPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Clavichord")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Clavichord", "Clv.")

    midiInstrument = 'clav'


class Organ(KeyboardPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Organ")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Organ", "Org.")

    midiInstrument = 'church organ'
    midiInstruments = (
        'drawbar organ',
        'percussive organ',
        'rock organ',
        'church organ',
        'reed organ',
    )

    def createWidgets(self, layout):
        super().createWidgets(layout)
        grid = layout.itemAt(layout.count() - 2).layout()
        self.pedalVoices = QSpinBox(minimum=0, maximum=4, value=1)
        self.pedalVoicesLabel = QLabel()
        self.pedalVoicesLabel.setBuddy(self.pedalVoices)
        grid.addWidget(self.pedalVoicesLabel, 2, 0)
        grid.addWidget(self.pedalVoices)

    def translateWidgets(self):
        super().translateWidgets()
        self.pedalVoicesLabel.setText(_("Pedal:"))
        self.pedalVoices.setToolTip(_(
            "Set to 0 to disable the pedal altogether."))

    def build(self, data, builder):
        super().build(data, builder)
        if self.pedalVoices.value():
            data.nodes.append(self.buildStaff(data, builder,
                'pedal', -1, self.pedalVoices.value(), clef="bass"))



class Celesta(KeyboardPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Celesta")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Celesta", "Cel.")

    midiInstrument = 'celesta'


class SynthPart(KeyboardPart):
    """Base class for synth parts.

    This is similar to _base.PianoStaffPart, except either
    upperVoices or lowerVoices can be set to zero, creating
    a single staff for writing monophonic lines.
    """
    # Derived classes should only include the subset of instruments
    # appropriate for that part type.
    # For example, SynthLead only includes the lead instruments.
    midiInstruments = (
        'synth bass 1',
        'synth bass 2',
        'synthstrings 1',
        'synthstrings 2',
        'synth voice',
        'synthbrass 1',
        'synthbrass 2',
        'lead 1 (square)',
        'lead 2 (sawtooth)',
        'lead 3 (calliope)',
        'lead 4 (chiff)',
        'lead 5 (charang)',
        'lead 6 (voice)',
        'lead 7 (fifths)',
        'lead 8 (bass+lead)',
        'pad 1 (new age)',
        'pad 2 (warm)',
        'pad 3 (polysynth)',
        'pad 4 (choir)',
        'pad 5 (bowed)',
        'pad 6 (metallic)',
        'pad 7 (halo)',
        'pad 8 (sweep)',
        'fx 1 (rain)',
        'fx 2 (soundtrack)',
        'fx 3 (crystal)',
        'fx 4 (atmosphere)',
        'fx 5 (brightness)',
        'fx 6 (goblins)',
        'fx 7 (echoes)',
        'fx 8 (sci-fi)',
    )

    def createWidgets(self, layout):
        super().createWidgets(layout)

        self.upperVoices.setMinimum(0)
        self.lowerVoices.setMinimum(0)

    def translateWidgets(self):
        super().translateWidgets()
        self.upperVoices.setToolTip(_(
            "Set to 0 to disable the right-hand part altogether."))
        self.lowerVoices.setToolTip(_(
            "Set to 0 to disable the left-hand part altogether."))

    def build(self, data, builder):
        """ Setup structure for a 1- or 2-staff PianoStaff. """
        p = ly.dom.PianoStaff()
        builder.setInstrumentNamesFromPart(p, self, data)
        s = ly.dom.Sim(p)
        upperCount = self.upperVoices.value()
        lowerCount = self.lowerVoices.value()
        if upperCount and lowerCount:
            # add two staves, with a respective number of voices.
            self.buildStaff(data, builder, 'right', 1, upperCount, s)
            self.buildStaff(data, builder, 'left', 0, lowerCount, s, "bass")
        elif upperCount:
            self.buildStaff(data, builder, 'right', 1, upperCount, s)
        elif lowerCount:
            self.buildStaff(data, builder, 'left', 0, lowerCount, s, "bass")
        data.nodes.append(p)


class SynthLead(SynthPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Synth lead")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Synth lead", "Syn.Ld.")

    def createWidgets(self, layout):
        super().createWidgets(layout)

        # This is intended primarily for monophonic parts in treble clef,
        # so omit lower voices by default
        self.lowerVoices.setValue(0)

    midiInstrument = 'lead 1 (square)'
    midiInstruments = (
        'lead 1 (square)',
        'lead 2 (sawtooth)',
        'lead 3 (calliope)',
        'lead 4 (chiff)',
        'lead 5 (charang)',
        'lead 6 (voice)',
        'lead 7 (fifths)',
        'lead 8 (bass+lead)',
    )


class SynthPad(SynthPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Synth pad")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Synth pad", "Syn.Pad")

    midiInstrument = 'pad 2 (warm)'
    midiInstruments = (
        'pad 1 (new age)',
        'pad 2 (warm)',
        'pad 3 (polysynth)',
        'pad 4 (choir)',
        'pad 5 (bowed)',
        'pad 6 (metallic)',
        'pad 7 (halo)',
        'pad 8 (sweep)',
    )


class SynthBass(SynthPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Synth bass")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Synth bass", "Syn.Bass")

    def createWidgets(self, layout):
        super().createWidgets(layout)

        # This is intended primarily for monophonic parts in bass clef,
        # so omit upper voices by default
        self.upperVoices.setValue(0)

    midiInstrument = 'synth bass 1'
    midiInstruments = (
        'synth bass 1',
        'synth bass 2',
    )


class SynthStrings(SynthPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Synth strings")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Synth strings", "Syn.Str.")

    midiInstrument = 'synthstrings 1'
    midiInstruments = (
        'synthstrings 1',
        'synthstrings 2',
    )


class SynthBrass(SynthPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Synth brass")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Synth brass", "Syn.Br.")

    midiInstrument = 'synthbrass 1'
    midiInstruments = (
        'synthbrass 1',
        'synthbrass 2',
    )

class SynthFx(SynthPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Synth effects")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Synth effects", "Syn.Fx.")

    midiInstrument = 'fx 3 (crystal)'
    midiInstruments = (
        'fx 1 (rain)',
        'fx 2 (soundtrack)',
        'fx 3 (crystal)',
        'fx 4 (atmosphere)',
        'fx 5 (brightness)',
        'fx 6 (goblins)',
        'fx 7 (echoes)',
        'fx 8 (sci-fi)',
    )


register(
    lambda: _("Keyboard instruments"),
    [
        Piano,
        ElectricPiano,
        Harpsichord,
        Clavichord,
        Organ,
        Celesta,
        SynthLead,
        SynthPad,
        SynthBass,
        SynthStrings,
        SynthBrass,
        SynthFx,
    ])


