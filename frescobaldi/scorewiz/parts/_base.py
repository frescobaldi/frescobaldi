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
Base types for parts.
"""


import collections

from PyQt6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QHBoxLayout,
                             QLabel, QSpinBox)

import listmodel
import ly.dom


Category = collections.namedtuple("Category", "title items icon")


def translate(*args):
    """Translate the arguments using the application's language."""
    return _(*args)


class Base:
    """Base class for both Part and Container."""
    @staticmethod
    def title(_=translate):
        """Should return a title.

        If a translator is given, it is used instead of the builtin.

        """

    @staticmethod
    def short(_=translate):
        """Should return an abbreviated title.

        If a translator is given, it is used instead of the builtin.

        """

    def createWidgets(self, layout):
        """Should create widgets to adjust settings."""
        self.noSettingsLabel = QLabel()
        layout.addWidget(self.noSettingsLabel)

    def translateWidgets(self):
        """Should set the text in the widgets when the language changes."""
        self.noSettingsLabel.setText('({})'.format(_("No settings available.")))

    def accepts(self):
        """Should return a tuple of classes this part item accepts as child items."""
        return ()

    def build(self, data, builder):
        """Should populate the PartData (see build.py)."""
        data.nodes.append(ly.dom.Comment(f"Part {self.__class__.__name__}"))


class Part(Base):
    """Base class for Parts (that can't contain other parts)."""


class Container(Base):
    """Base class for "part" types that can contain others, like a Staff Group or Score, Book etc."""
    def accepts(self):
        return (Part, Container)


class Group(Container):
    """Base class for "part" types that are a group such as Book, BookPart and Score."""


# Mixin- or base classes with basic behaviour
class SingleVoicePart(Part):
    """Base class for a part creating a single single-voice staff."""
    midiInstrument = ''
    clef = None
    octave = 1
    transposition = None # or a three tuple (octave, note, alteration)

    def build(self, data, builder):
        a = data.assignMusic(None, self.octave)
        staff = ly.dom.Staff()
        builder.setInstrumentNamesFromPart(staff, self, data)
        if self.midiInstrument:
            builder.setMidiInstrument(staff, self.midiInstrument)
        seq = ly.dom.Seqr(staff)
        if self.clef:
            ly.dom.Clef(self.clef, seq)
        if self.transposition is not None:
            seq = builder.setStaffTransposition(seq, self.transposition)
        ly.dom.Identifier(a.name, seq)
        data.nodes.append(staff)


class PianoStaffPart(Part):
    """Base class for parts creating a piano staff."""
    midiInstruments = ()  # may contain a list of MIDI instruments.
    octave = 1  # for the right hand part; left is 1 octave lower.
    transposition = None

    # subclasses can override these as needed
    minUpperVoices = 1
    maxUpperVoices = 4
    defaultUpperVoices = 1
    minLowerVoices = 1
    maxLowerVoices = 4
    defaultLowerVoices = 1

    def createWidgets(self, layout):
        self.label = QLabel(wordWrap=True)
        self.upperVoicesLabel = QLabel()
        self.lowerVoicesLabel = QLabel()
        self.upperVoices = QSpinBox(minimum=self.minUpperVoices,
                                    maximum=self.maxUpperVoices,
                                    value=self.defaultUpperVoices)
        self.lowerVoices = QSpinBox(minimum=self.minLowerVoices,
                                    maximum=self.maxUpperVoices,
                                    value=self.defaultLowerVoices)
        self.dynamicsStaff = QCheckBox()
        self.dynamicsStaff.setChecked(True)

        self.upperVoicesLabel.setBuddy(self.upperVoices)
        self.lowerVoicesLabel.setBuddy(self.lowerVoices)

        layout.addWidget(self.label)
        grid = QGridLayout()
        grid.addWidget(self.upperVoicesLabel, 0, 0)
        grid.addWidget(self.upperVoices, 0, 1)
        grid.addWidget(self.lowerVoicesLabel, 1, 0)
        grid.addWidget(self.lowerVoices, 1, 1)
        layout.addLayout(grid)
        layout.addWidget(self.dynamicsStaff)

        if self.midiInstruments:
            self.createMidiInstrumentWidgets(layout)

        self.upperVoices.valueChanged.connect(self._voiceCountChanged)
        self.lowerVoices.valueChanged.connect(self._voiceCountChanged)
        self._voiceCountChanged()

    def createMidiInstrumentWidgets(self, layout):
        self.midiInstrumentLabel = QLabel()
        self.midiInstrumentSelection = QComboBox()
        self.midiInstrumentSelection.addItems(self.midiInstruments)
        self.midiInstrumentSelection.setCurrentIndex(
            self.midiInstruments.index(self.midiInstrument))
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.midiInstrumentLabel)
        box.addWidget(self.midiInstrumentSelection)

    def translateWidgets(self):
        self.label.setText('{} <i>({})</i>'.format(
            _("Adjust how many separate voices you want on each staff."),
            _("This is primarily useful when you write polyphonic music "
              "like a fugue.")))
        self.upperVoicesLabel.setText(_("Right hand:"))
        self.lowerVoicesLabel.setText(_("Left hand:"))
        self.dynamicsStaff.setText(_("Center dynamics between staffs"))
        if self.midiInstruments:
            self.translateMidiInstrumentWidgets()

    def translateMidiInstrumentWidgets(self):
        self.midiInstrumentLabel.setText(_("MIDI instrument:"))

    def buildStaff(self, data, builder, name, octave, numVoices=1, node=None, clef=None):
        """Build a staff with the given number of voices and name."""
        staff = ly.dom.Staff(name, parent=node)
        if self.midiInstruments:
            midiInstrument = self.midiInstrumentSelection.currentText()
            if midiInstrument == 'percussive organ' and name != 'right':
                # The Hammond B3, which this MIDI instrument is intended
                # to emulate, only supports percussion on the upper manual
                midiInstrument = 'drawbar organ'
            builder.setMidiInstrument(staff, midiInstrument)
        else:
            builder.setMidiInstrument(staff, self.midiInstrument)
        c = ly.dom.Seqr(staff)
        if clef:
            ly.dom.Clef(clef, c)
        if self.transposition is not None:
            c = builder.setStaffTransposition(c, self.transposition)
        if numVoices == 1:
            a = data.assignMusic(name, octave)
            ly.dom.Identifier(a.name, c)
        else:
            c = ly.dom.Sim(c)
            for i in range(1, numVoices):
                a = data.assignMusic(name + ly.util.int2text(i), octave)
                ly.dom.Identifier(a.name, c)
                ly.dom.VoiceSeparator(c)
            a = data.assignMusic(name + ly.util.int2text(numVoices), octave)
            ly.dom.Identifier(a.name, c)
        return staff

    def buildDynamicsStaff(self, data, pianoSim):
        """Build a special staff to display dynamics."""
        dynamicsStaff = ly.dom.Dynamics(parent=pianoSim)
        a = data.assign('dynamics')
        ly.dom.Identifier(a.name, dynamicsStaff)
        s = ly.dom.Seq(a)
        ly.dom.Identifier(data.globalName, s).after = 1
        ly.dom.LineComment(_("Dynamics follow here."), s)
        ly.dom.BlankLine(s)

    def build(self, data, builder):
        """ Setup structure for a 1- or 2-staff PianoStaff. """
        p = ly.dom.PianoStaff()
        builder.setInstrumentNamesFromPart(p, self, data)
        s = ly.dom.Sim(p)
        upperCount = self.upperVoices.value()
        lowerCount = self.lowerVoices.value()
        if upperCount and lowerCount:
            # add two staves, with a respective number of voices.
            self.buildStaff(data, builder, 'right', self.octave, upperCount, s)
            if self.dynamicsStaff.isChecked():
                # both staffs have to be present to use this feature
                self.buildDynamicsStaff(data, s)
            self.buildStaff(data, builder, 'left', self.octave - 1, lowerCount, s, "bass")
        elif upperCount:
            # add the treble staff only
            self.buildStaff(data, builder, 'right', self.octave, upperCount, s)
        elif lowerCount:
            # add the bass staff only
            self.buildStaff(data, builder, 'left', self.octave - 1, lowerCount, s, "bass")
        data.nodes.append(p)

    def _voiceCountChanged(self, value=None):
        """Called when the number of voices in a staff is changed."""
        # Make sure we always have at least one voice present (this is mainly
        # for the synth parts that allow setting either count to zero)
        self.upperVoices.setMinimum(
            self.minUpperVoices if self.lowerVoices.value() else 1)
        self.lowerVoices.setMinimum(
            self.minLowerVoices if self.upperVoices.value() else 1)
        # Enable the option to center dynamics only when two staffs are present
        self.dynamicsStaff.setEnabled(
            self.upperVoices.value() and self.lowerVoices.value())


class ChordNames:
    def createWidgets(self, layout):
        self.chordStyleLabel = QLabel()
        self.chordStyle = QComboBox()
        self.chordStyleLabel.setBuddy(self.chordStyle)
        self.chordStyle.setModel(listmodel.ListModel(chordNameStyles, self.chordStyle,
            display=listmodel.translate))
        self.guitarFrets = QCheckBox()

        box = QHBoxLayout()
        box.addWidget(self.chordStyleLabel)
        box.addWidget(self.chordStyle)
        layout.addLayout(box)
        layout.addWidget(self.guitarFrets)

    def translateWidgets(self):
        self.chordStyleLabel.setText(_("Chord style:"))
        self.guitarFrets.setText(_("Guitar fret diagrams"))
        self.guitarFrets.setToolTip(_(
            "Show predefined guitar fret diagrams below the chord names "
            "(LilyPond 2.12 and above)."))
        self.chordStyle.model().update()

    def build(self, data, builder):
        p = ly.dom.ChordNames()
        a = data.assign('chordNames')
        ly.dom.Identifier(a.name, p)
        s = ly.dom.ChordMode(a)
        ly.dom.Identifier(data.globalName, s).after = 1
        i = self.chordStyle.currentIndex()
        if i > 0:
            ly.dom.Line('\\{}Chords'.format(
                ('german', 'semiGerman', 'italian', 'french')[i-1]), s)
        ly.dom.LineComment(_("Chords follow here."), s)
        ly.dom.BlankLine(s)
        data.nodes.append(p)
        if self.guitarFrets.isChecked():
            f = ly.dom.FretBoards()
            ly.dom.Identifier(a.name, f)
            data.nodes.append(f)
            data.includes.append("predefined-guitar-fretboards.ly")


chordNameStyles = (
    lambda: _("Default"),
    lambda: _("German"),
    lambda: _("Semi-German"),
    lambda: _("Italian"),
    lambda: _("French"),
)

