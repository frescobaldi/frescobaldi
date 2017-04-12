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
Brass part types.
"""


from . import _base
from . import register


class BrassPart(_base.SingleVoicePart):
    """Base class for brass types."""


class HornF(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Horn in F")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Horn in F", "Hn.F.")

    midiInstrument = 'french horn'
    transposition = (-1, 3, 0)


class TrumpetC(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Trumpet in C")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Trumpet in C", "Tr.C.")

    midiInstrument = 'trumpet'


class TrumpetBb(TrumpetC):
    @staticmethod
    def title(_=_base.translate):
        return _("Trumpet in Bb")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Trumpet in Bb", "Tr.Bb.")

    transposition = (-1, 6, -1)


class CornetBb(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Cornet in Bb")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Cornet in Bb", "Crt.Bb.")

    transposition = (-1, 6, -1)


class Flugelhorn(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Flugelhorn")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Flugelhorn", "Fgh.")

    midiInstrument = 'trumpet'


class Mellophone(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Mellophone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Mellophone", "Mph.")

    midiInstrument = 'french horn'
    transposition = (-1, 3, 0)


class Trombone(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Trombone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Trombone", "Trb.")

    midiInstrument = 'trombone'
    clef = 'bass'
    octave = -1


class Baritone(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Baritone")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Baritone", "Bar.")

    midiInstrument = 'trombone'
    clef = 'bass'
    octave = -1


class Euphonium(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Euphonium")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Euphonium", "Euph.")

    midiInstrument = 'trombone'
    clef = 'bass'
    octave = -1


class Tuba(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Tuba")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Tuba", "Tb.")

    midiInstrument = 'tuba'
    transposition = (-2, 6, -1)


class BassTuba(BrassPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bass Tuba")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bass Tuba", "B.Tb.")

    midiInstrument = 'tuba'
    clef = 'bass'
    octave = -1
    transposition = (-2, 0, 0)


register(
    lambda: _("Brass"),
    [
        HornF,
        TrumpetC,
        TrumpetBb,
        CornetBb,
        Flugelhorn,
        Mellophone,
        Trombone,
        Baritone,
        Euphonium,
        Tuba,
        BassTuba,
    ])
