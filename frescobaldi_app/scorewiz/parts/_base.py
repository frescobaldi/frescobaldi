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

from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QHBoxLayout,
                             QLabel, QSpinBox)

import listmodel
import ly.dom


Category = collections.namedtuple("Category", "title items icon")


def translate(*args):
    """Translate the arguments using the application's language."""
    return _(*args)


class Base(object):
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
        self.noSettingsLabel.setText('({0})'.format(_("No settings available.")))

    def accepts(self):
        """Should return a tuple of classes this part item accepts as child items."""
        return ()

    def build(self, data, builder):
        """Should populate the PartData (see build.py)."""
        data.nodes.append(ly.dom.Comment("Part {0}".format(self.__class__.__name__)))


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
        a = data.assignMusic(None, self.octave, self.transposition)
        staff = ly.dom.Staff()
        builder.setInstrumentNamesFromPart(staff, self, data)
        if self.midiInstrument:
            builder.setMidiInstrument(staff, self.midiInstrument)
        seq = ly.dom.Seqr(staff)
        if self.clef:
            ly.dom.Clef(self.clef, seq)
        ly.dom.Identifier(a.name, seq)
        data.nodes.append(staff)


class PianoStaffPart(Part):
    """Base class for parts creating a piano staff."""
    def createWidgets(self, layout):
        self.label = QLabel(wordWrap=True)
        self.upperVoicesLabel = QLabel()
        self.lowerVoicesLabel = QLabel()
        self.upperVoices = QSpinBox(minimum=1, maximum=4, value=1)
        self.lowerVoices = QSpinBox(minimum=1, maximum=4, value=1)

        self.upperVoicesLabel.setBuddy(self.upperVoices)
        self.lowerVoicesLabel.setBuddy(self.lowerVoices)

        layout.addWidget(self.label)
        grid = QGridLayout()
        grid.addWidget(self.upperVoicesLabel, 0, 0)
        grid.addWidget(self.upperVoices, 0, 1)
        grid.addWidget(self.lowerVoicesLabel, 1, 0)
        grid.addWidget(self.lowerVoices, 1, 1)
        layout.addLayout(grid)

    def translateWidgets(self):
        self.label.setText('{0} <i>({1})</i>'.format(
            _("Adjust how many separate voices you want on each staff."),
            _("This is primarily useful when you write polyphonic music "
              "like a fuge.")))
        self.upperVoicesLabel.setText(_("Right hand:"))
        self.lowerVoicesLabel.setText(_("Left hand:"))

    def buildStaff(self, data, builder, name, octave, numVoices=1, node=None, clef=None):
        """Build a staff with the given number of voices and name."""
        staff = ly.dom.Staff(name, parent=node)
        builder.setMidiInstrument(staff, self.midiInstrument)
        c = ly.dom.Seqr(staff)
        if clef:
            ly.dom.Clef(clef, c)
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

    def build(self, data, builder):
        """ Setup structure for a 2-staff PianoStaff. """
        p = ly.dom.PianoStaff()
        builder.setInstrumentNamesFromPart(p, self, data)
        s = ly.dom.Sim(p)
        # add two staves, with a respective number of voices.
        self.buildStaff(data, builder, 'right', 1, self.upperVoices.value(), s)
        self.buildStaff(data, builder, 'left', 0, self.lowerVoices.value(), s, "bass")
        data.nodes.append(p)


class ChordNames(object):
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
            ly.dom.Line('\\{0}Chords'.format(
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

