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

from __future__ import unicode_literals

import __builtin__

from PyQt4.QtCore import QRegExp, Qt
from PyQt4.QtGui import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QRegExpValidator,
    QSpinBox, QVBoxLayout)

import listmodel
import ly.dom

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
    
    def assignLyrics(self, data, name, verse=0):
        """Creates an empty assignment for lyrics.
        
        Returns the assignment.
        
        """
        l = ly.dom.LyricMode()
        if verse:
            name = name + ly.util.int2text(verse)
            ly.dom.Line('\\set stanza = "{0}."'.format(verse), l)
        a = data.assign(name)
        a.append(l)
        ly.dom.LineComment(_("Lyrics follow here."), l)
        ly.dom.BlankLine(l)
        return a
    
    def addStanzas(self, data, node):
        """Add stanzas to the given (Voice) node.
        
        The stanzas (as configured in self.stanzas.value()) are added
        using \\addlyrics.
        
        """
        if self.stanzas.value() == 1:
            ly.dom.Identifier(self.assignLyrics(data, 'verse').name, ly.dom.AddLyrics(node))
        else:
            for i in range(self.stanzas.value()):
                ly.dom.Identifier(self.assignLyrics(data, 'verse', i + 1).name, ly.dom.AddLyrics(node))


class VocalSoloPart(VocalPart, _base.SingleVoicePart):
    """Base class for vocal solo parts."""
    octave = 1
    clef = None
    
    def build(self, data, builder):
        super(VocalSoloPart, self).build(data, builder)
        stub = data.assignments[-1][0][-1]
        stub.insert(1, ly.dom.Line('\\dynamicUp')) # just after the \global
        staff = data.nodes[-1]
        staff[-1].may_remove_brackets = False
        self.addStanzas(data, staff)
        if self.ambitus.isChecked():
            ly.dom.Line('\\consists "Ambitus_engraver"', staff.getWith())


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

    def build(self, data, builder):
        """Create chord names, song and lyrics.
        
        Optionally a second staff with a piano accompaniment.
        
        """
        if self.chords.isChecked():
            _base.ChordNames.build(self, data, builder)
        if self.accomp.isChecked():
            p = ly.dom.ChoirStaff()
            #TODO: instrument names ?
            #TODO: different midi instrument for voice and accompaniment ?
            s = ly.dom.Sim(p)
            mel = ly.dom.Sim(ly.dom.Staff(parent=s))
            v1 = ly.dom.Voice(parent=mel)
            s1 = ly.dom.Seq(v1)
            ly.dom.Text('\\voiceOne', s1)
            a = data.assignMusic('melody', 1)
            ly.dom.Identifier(a.name, s1)
            s2 = ly.dom.Seq(ly.dom.Voice(parent=mel))
            ly.dom.Text('\\voiceTwo', s2)
            a = data.assignMusic('accRight', 0)
            ly.dom.Identifier(a.name, s2)
            acc = ly.dom.Seq(ly.dom.Staff(parent=s))
            ly.dom.Clef('bass', acc)
            a = data.assignMusic('accLeft', -1)
            ly.dom.Identifier(a.name, acc)
            if self.ambitus.isChecked():
                # We can't use \addlyrics when the voice has a \with {}
                # section, because it creates a nested Voice context.
                # So if the ambitus engraver should be added to the Voice,
                # we don't use \addlyrics but create a new Lyrics context.
                # So in that case we don't use addStanzas, but insert the
                # Lyrics contexts manually inside our ChoirStaff.
                v1.cid = ly.dom.Reference('melody')
                ly.dom.Line('\\consists "Ambitus_engraver"', v1.getWith())
                count = self.stanzas.value() # number of stanzas
                if count == 1:
                    l = ly.dom.Lyrics()
                    s.insert(acc.parent(), l)
                    a = self.assignLyrics(data, 'verse')
                    ly.dom.Identifier(a.name, ly.dom.LyricsTo(v1.cid, l))
                else:
                    for i in range(count):
                        l = ly.dom.Lyrics()
                        s.insert(acc.parent(), l)
                        a = self.assignLyrics(data, 'verse', i + 1)
                        ly.dom.Identifier(a.name, ly.dom.LyricsTo(v1.cid, l))
            else:
                self.addStanzas(data, v1)
        else:
            a = data.assignMusic('melody', 1)
            p = ly.dom.Staff()
            ly.dom.Identifier(a.name, ly.dom.Seq(p))
            self.addStanzas(data, p)
            if self.ambitus.isChecked():
                ly.dom.Line('\\consists "Ambitus_engraver"', p.getWith())
        data.nodes.append(p)


class Choir(VocalPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Choir")

    def createWidgets(self, layout):
        self.label = QLabel(wordWrap=True)
        self.voicingLabel = QLabel()
        self.voicing = QComboBox(editable=True)
        self.voicingLabel.setBuddy(self.voicing)
        self.voicing.setCompleter(None)
        self.voicing.setValidator(QRegExpValidator(
            QRegExp("[SATB]+(-[SATB]+)*", Qt.CaseInsensitive), self.voicing))
        self.voicing.addItems((
            'SA-TB', 'S-A-T-B',
            'SA', 'S-A', 'SS-A', 'S-S-A',
            'TB', 'T-B', 'TT-B', 'T-T-B',
            'SS-A-T-B', 'S-A-TT-B', 'SS-A-TT-B',
            'S-S-A-T-T-B', 'S-S-A-A-T-T-B-B',
            ))
        self.lyricsLabel = QLabel()
        self.lyrics = QComboBox()
        self.lyricsLabel.setBuddy(self.lyrics)
        self.lyrics.setModel(listmodel.ListModel(lyricStyles, self.lyrics,
            display=listmodel.translate_index(0),
            tooltip=listmodel.translate_index(1)))
        self.lyrics.setCurrentIndex(0)
        self.pianoReduction = QCheckBox()
        self.rehearsalMidi = QCheckBox()
        
        layout.addWidget(self.label)
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.voicingLabel)
        box.addWidget(self.voicing)
        self.createStanzaWidget(layout)
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.lyricsLabel)
        box.addWidget(self.lyrics)
        self.createAmbitusWidget(layout)
        layout.addWidget(self.pianoReduction)
        layout.addWidget(self.rehearsalMidi)
    
    def translateWidgets(self):
        self.translateStanzaWidget()
        self.translateAmbitusWidget()
        self.lyrics.model().update()
        self.label.setText('<p>{0} <i>({1})</i></p>'.format(
            _("Please select the voices for the choir. "
              "Use the letters S, A, T, or B. A hyphen denotes a new staff."),
            _("Hint: For a double choir you can use two choir parts.")))
        self.voicingLabel.setText(_("Voicing:"))
        self.lyricsLabel.setText(_("Lyrics:"))
        self.pianoReduction.setText(_("Piano reduction"))
        self.pianoReduction.setToolTip(_(
            "Adds an automatically generated piano reduction."))
        self.rehearsalMidi.setText(_("Rehearsal MIDI files"))
        self.rehearsalMidi.setToolTip(_(
            "Creates a rehearsal MIDI file for every voice, "
            "even if no MIDI output is generated for the main score."))



lyricStyles = (
    (lambda: _("All voices same lyrics"),
        lambda: _("A set of the same lyrics is placed between all staves.")),
    (lambda: _("Every voice same lyrics"),
        lambda: _("Every voice gets its own lyrics, using the same text as the"
                  " other voices.")),
    (lambda: _("Every voice different lyrics"),
        lambda: _("Every voice gets a different set of lyrics.")),
    (lambda: _("Distribute stanzas"),
        lambda: _("One set of stanzas is distributed across the staves.")),
)



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

