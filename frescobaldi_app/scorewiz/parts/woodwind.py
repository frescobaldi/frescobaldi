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
Wood wind part types.
"""


from . import _base
from . import register


class WoodWindPart(_base.SingleVoicePart):
    """Base class for wood wind part types."""


class Flute(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Flute")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Flute", "Fl.")

    midiInstrument = 'flute'


class Piccolo(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Piccolo")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Piccolo", "Pic.")

    midiInstrument = 'piccolo'
    octave = 2
    transposition = (1, 0, 0)


class AltoFlute(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Alto flute")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Alto flute", "A.Fl.")

    midiInstrument = 'flute'
    octave = 0
    transposition = (-1, 4, 0)


class BassFlute(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bass flute")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bass flute", "Bfl.")

    midiInstrument = 'flute'
    octave = 0
    transposition = (-1, 0, 0)


class Oboe(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Oboe")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Oboe", "Ob.")

    midiInstrument = 'oboe'


class OboeDAmore(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Oboe d'amore")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Oboe d'amore", "Ob.d'am.")

    midiInstrument = 'oboe'
    octave = 0
    transposition = (-1, 5, 0)


class EnglishHorn(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("English horn")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for English horn", "Eng.h.")

    midiInstrument = 'english horn'
    octave = 0
    transposition = (-1, 3, 0)


class Bassoon(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bassoon")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bassoon", "Bn.")

    midiInstrument = 'bassoon'
    clef = 'bass'
    octave = -1


class ContraBassoon(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Contrabassoon")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Contrabassoon", "C.Bn.")

    midiInstrument = 'bassoon'
    transposition = (-1, 0, 0)
    clef = 'bass'
    octave = -2


class Clarinet(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Clarinet")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Clarinet", "Cl.")

    midiInstrument = 'clarinet'
    transposition = (-1, 6, -1)


class EflatClarinet(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("E-flat clarinet")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for E-flat clarinet", "Cl. in Eb")

    midiInstrument = 'clarinet'
    transposition = (0, 2, -1)


class AClarinet(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("A clarinet")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for A clarinet", "Cl. in A")

    midiInstrument = 'clarinet'
    octave = 0
    transposition = (-1, 5, 0)


class BassClarinet(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bass clarinet")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bass clarinet", "B.Cl.")

    midiInstrument = 'clarinet'
    octave = -1
    transposition = (-2, 6, -1)


class C_MelodySax(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("C-melody saxophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for C-melody saxophone", "C-Mel Sax")

    midiInstrument = 'soprano sax'


class SopraninoSax(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Sopranino saxophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Sopranino saxophone", "Si.Sax.")

    midiInstrument = 'soprano sax'
    transposition = (0, 2, -1)    # es'


class SopranoSax(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Soprano saxophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Soprano saxophone", "So.Sax.")

    midiInstrument = 'soprano sax'
    transposition = (-1, 6, -1)   # bes


class AltoSax(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Alto saxophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Alto saxophone", "A.Sax.")

    midiInstrument = 'alto sax'
    octave = 0
    transposition = (-1, 2, -1)   # es


class TenorSax(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Tenor saxophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Tenor saxophone", "T.Sax.")

    midiInstrument = 'tenor sax'
    octave = 0
    transposition = (-2, 6, -1)   # bes,


class BaritoneSax(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Baritone saxophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Baritone saxophone", "B.Sax.")

    midiInstrument = 'baritone sax'
    octave = -1
    transposition = (-2, 2, -1)   # es,


class BassSax(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bass saxophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bass saxophone", "Bs.Sax.")

    midiInstrument = 'baritone sax'
    octave = -1
    transposition = (-3, 6, -1)   # bes,,


class SopraninoRecorder(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Sopranino recorder")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Sopranino recorder", "Si.Rec.")

    midiInstrument = 'recorder'
    octave = 2
    transposition = (1, 0, 0)

class SopranoRecorder(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Soprano recorder")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Soprano recorder", "S.Rec.")

    midiInstrument = 'recorder'
    octave = 2
    transposition = (1, 0, 0)


class AltoRecorder(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Alto recorder")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Alto recorder", "A.Rec.")

    midiInstrument = 'recorder'


class TenorRecorder(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Tenor recorder")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Tenor recorder", "T.Rec.")

    midiInstrument = 'recorder'


class BassRecorder(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bass recorder")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bass recorder", "B.Rec.")

    midiInstrument = 'recorder'
    clef = 'bass'
    octave = 0
    transposition = (1, 0, 0)


class ContraBassRecorder(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Contrabass recorder")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Contrabass recorder", "Cb.Rec.")

    midiInstrument = 'recorder'
    clef = 'bass'
    octave = -1


class SubContraBassRecorder(WoodWindPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Subcontrabass recorder")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Subcontrabass recorder", "Scb.Rec.")

    midiInstrument = 'recorder'
    clef = 'bass'
    octave = -2
    transposition = (-1, 0, 0)



register(
    lambda: _("Woodwinds"),
    [
        Flute,
        Piccolo,
        AltoFlute,
        BassFlute,
        Oboe,
        OboeDAmore,
        EnglishHorn,
        Bassoon,
        ContraBassoon,
        Clarinet,
        EflatClarinet,
        AClarinet,
        BassClarinet,
        SopraninoSax,
        SopranoSax,
        AltoSax,
        TenorSax,
        BaritoneSax,
        BassSax,
        C_MelodySax,
        SopraninoRecorder,
        SopranoRecorder,
        AltoRecorder,
        TenorRecorder,
        BassRecorder,
        ContraBassRecorder,
        SubContraBassRecorder
    ])
