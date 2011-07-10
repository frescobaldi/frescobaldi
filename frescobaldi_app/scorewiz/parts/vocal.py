# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Vocal part types.
"""

import __builtin__

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import _base
from . import register


class VocalPart(_base.Part):
    """Base class for vocal parts."""
    midiInstrument = 'choir aahs'

    def createWidgets(self, layout):
        self.createStanzaWidget(layout)
        self.createAmbitusWidget(layout)
        
    def translateWidgets(self):
        self.translateStanzaWidget()
        self.translateAmbitusWidget()
        
    def createStanzaWidget(self, layout):
        self.stanzas = QSpinBox(minimum=1, maximum=99, value=1)
        self.stanzasLabel = QLabel()
        self.stanzasLabel.setBuddy(self.stanzas)
        box = QHBoxLayout(spacing=0)
        box.addWidget(self.stanzasLabel)
        box.addWidget(self.stanzas)
        layout.addLayout(box)
        
    def translateStanzaWidget(self):
        self.stanzasLabel.setText(_("Stanzas:"))
        self.stanzas.setToolTip(_("The number of stanzas."))
    
    def createAmbitusWidget(self, layout):
        self.ambitus = QCheckBox()
        layout.addWidget(self.ambitus)
        
    def translateAmbitusWidget(self):
        self.ambitus.setText(_("Ambitus"))
        self.ambitus.setToolTip(_(
            "Show the pitch range of the voice at the beginning of the staff."))


class VocalSoloPart(VocalPart):
    """Base class for vocal solo parts."""
    octave = 1
    clef = None

class SopranoVoice(VocalSoloPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Soprano")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Soprano", "S.")


class MezzoSopranoVoice(VocalSoloPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Mezzo-soprano")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Mezzo-soprano", "Ms.")


class AltoVoice(VocalSoloPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Alto")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Alto", "A.")
    
    octave = 0


class TenorVoice(VocalSoloPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Tenor")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Tenor", "T.")

    octave = 0
    clef = 'treble_8'


class BassVoice(VocalSoloPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Bass")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Bass", "B.")

    octave = -1
    clef = 'bass'


class LeadSheet(VocalPart, _base.ChordNames):
    @staticmethod
    def title(_=__builtin__._):
        return _("Lead sheet")
    
    def createWidgets(self, layout):
        self.label = QLabel(wordWrap=True)
        self.chords = QGroupBox(checkable=True, checked=True)
        layout.addWidget(self.label)
        layout.addWidget(self.chords)
        box = QVBoxLayout()
        self.chords.setLayout(box)
        _base.ChordNames.createWidgets(self, box)
        self.accomp = QCheckBox()
        layout.addWidget(self.accomp)
        VocalPart.createWidgets(self, layout)
    
    def translateWidgets(self):
        VocalPart.translateWidgets(self)
        _base.ChordNames.translateWidgets(self)
        self.label.setText('<i>{0}</i>'.format(_(
            "The Lead Sheet provides a staff with chord names above "
            "and lyrics below it. A second staff is optional.")))
        self.chords.setTitle(_("Chord names"))
        self.accomp.setText(_("Add accompaniment staff"))
        self.accomp.setToolTip(_(
            "Adds an accompaniment staff and also puts an accompaniment "
            "voice in the upper staff."))



class Choir(VocalPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Choir")

    #def widgets(self, layout):
        #l = QLabel('<p>{0} <i>({1})</i></p>'.format(
            #i18n("Please select the voices for the choir. "
            #"Use the letters S, A, T, or B. A hyphen denotes a new staff."),
            #i18n("Hint: For a double choir you can use two choir parts.")))
        #l.setWordWrap(True)
        #layout.addWidget(l)
        #h = KHBox()
        #layout.addWidget(h)
        #l = QLabel(i18n("Voicing:"), h)
        #self.voicing = QComboBox(h)
        #l.setBuddy(self.voicing)
        #self.voicing.setEditable(True)
        #self.voicing.setCompleter(None)
        #self.voicing.setValidator(QRegExpValidator(
            #QRegExp("[SATB]+(-[SATB]+)*", Qt.CaseInsensitive), self.voicing))
        #self.voicing.addItems((
            #'SA-TB', 'S-A-T-B',
            #'SA', 'S-A', 'SS-A', 'S-S-A',
            #'TB', 'T-B', 'TT-B', 'T-T-B',
            #'SS-A-T-B', 'S-A-TT-B', 'SS-A-TT-B',
            #'S-S-A-T-T-B', 'S-S-A-A-T-T-B-B',
            #))
        #self.stanzaWidget(layout)
        #h = KHBox()
        #layout.addWidget(h)
        #l = QLabel(i18n("Lyrics:"), h)
        #self.lyrics = QComboBox(h)
        #l.setBuddy(self.lyrics)
        #for index, (text, tooltip) in enumerate((
         #(i18n("All voices same lyrics"),
          #i18n("A set of the same lyrics is placed between all staves.")),
         #(i18n("Every voice same lyrics"),
          #i18n("Every voice gets its own lyrics, using the same text as the"
               #" other voices.")),
         #(i18n("Every voice different lyrics"),
          #i18n("Every voice gets a different set of lyrics.")),
         #(i18n("Distribute stanzas"),
          #i18n("One set of stanzas is distributed across the staves.")))):
            #self.lyrics.addItem(text)
            #self.lyrics.setItemData(index, tooltip, Qt.ToolTipRole)
        #self.lyrics.setCurrentIndex(0)
        #self.ambitusWidget(layout)
        #self.pianoReduction = QCheckBox(i18n("Piano reduction"))
        #self.pianoReduction.setToolTip(i18n(
            #"Adds an automatically generated piano reduction."))
        #layout.addWidget(self.pianoReduction)
        #self.rehearsalMidi = QCheckBox(i18n("Rehearsal MIDI files"))
        #self.rehearsalMidi.setToolTip(i18n(
            #"Creates a rehearsal MIDI file for every voice, "
            #"even if no MIDI output is generated for the main score."))
        #layout.addWidget(self.rehearsalMidi)

    #identifiers = {
        #'S': 'soprano',
        #'A': 'alto',
        #'T': 'tenor',
        #'B': 'bass',
    #}
    
    #octaves = {
        #'S': SopranoVoice.octave,
        #'A': AltoVoice.octave,
        #'T': TenorVoice.octave,
        #'B': BassVoice.octave,
    #}
    
    #instrumentNames = {
        #'S': SopranoVoice.instrumentNames,
        #'A': AltoVoice.instrumentNames,
        #'T': TenorVoice.instrumentNames,
        #'B': BassVoice.instrumentNames,
    #}
            

register(
    lambda: _("Vocal"),
    [
        LeadSheet,
        SopranoVoice,
        MezzoSopranoVoice,
        AltoVoice,
        TenorVoice,
        BassVoice,
        Choir,
    ])

