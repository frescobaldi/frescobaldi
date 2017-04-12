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
Plucked string part types.
"""


from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QCompleter, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox,
)

import listmodel
import completionmodel
import ly.dom

from . import _base
from . import register


class TablaturePart(_base.Part):
    """Base class for tablature instrument part types."""

    octave = 0
    clef = None
    transposition = None
    tunings = ()    # may contain a list of tunings.
    tabFormat = ''  # can contain a tablatureFormat value.

    def createWidgets(self, layout):
        self.staffTypeLabel = QLabel()
        self.staffType = QComboBox()
        self.staffTypeLabel.setBuddy(self.staffType)
        self.staffType.setModel(listmodel.ListModel(tablatureStaffTypes,
            self.staffType, display=listmodel.translate))
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.staffTypeLabel)
        box.addWidget(self.staffType)
        if self.tunings:
            self.createTuningWidgets(layout)
            self.staffType.activated.connect(self.slotTabEnable)
            self.slotTabEnable(0)

    def createTuningWidgets(self, layout):
        self.tuningLabel = QLabel()
        self.tuning = QComboBox()
        self.tuningLabel.setBuddy(self.tuning)
        tunings = [('', lambda: _("Default"))]
        tunings.extend(self.tunings)
        tunings.append(('', lambda: _("Custom tuning")))
        self.tuning.setModel(listmodel.ListModel(tunings, self.tuning,
            display=listmodel.translate_index(1)))
        self.tuning.setCurrentIndex(1)
        self.customTuning = QLineEdit(enabled=False)
        completionmodel.complete(self.customTuning,
            "scorewiz/completion/plucked_strings/custom_tuning")
        self.tuning.currentIndexChanged.connect(self.slotCustomTuningEnable)
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.tuningLabel)
        box.addWidget(self.tuning)
        layout.addWidget(self.customTuning)

    def translateWidgets(self):
        self.staffTypeLabel.setText(_("Staff type:"))
        self.staffType.model().update()
        if self.tunings:
            self.translateTuningWidgets()

    def translateTuningWidgets(self):
        self.tuningLabel.setText(_("Tuning:"))
        self.customTuning.setToolTip('<qt>' + _(
            "Select custom tuning in the combobox and "
            "enter a custom tuning here, e.g. <code>e, a d g b e'</code>. "
            "Use absolute note names in the same language as you want to use "
            "in your document (by default: \"nederlands\")."))
        try:
            self.customTuning.setPlaceholderText(_("Custom tuning..."))
        except AttributeError:
            pass # only in Qt 4.7+
        self.tuning.model().update()

    def slotTabEnable(self, enable):
        """Called when the user changes the staff type.

        Non-zero if the user wants a TabStaff.

        """
        self.tuning.setEnabled(bool(enable))
        if enable:
            self.slotCustomTuningEnable(self.tuning.currentIndex())
        else:
            self.customTuning.setEnabled(False)

    def slotCustomTuningEnable(self, index):
        self.customTuning.setEnabled(index > len(self.tunings))

    def voiceCount(self):
        """Returns the number of voices.

        Inherit to make this user-settable.

        """
        return 1

    def build(self, data, builder):
        # First make assignments for the voices we want to create
        numVoices = self.voiceCount()
        if numVoices == 1:
            voices = (ly.util.mkid(data.name()),)
        elif numVoices == 2:
            order = 1, 2
            voices = 'upper', 'lower'
        elif numVoices == 3:
            order = 1, 3, 2
            voices = 'upper', 'middle', 'lower'
        else:
            order = 1, 2, 3, 4
            voices = [ly.util.mkid(data.name(), "voice") + ly.util.int2text(i) for i in order]

        assignments = [data.assignMusic(name, self.octave, self.transposition)
                       for name in voices]

        staffType = self.staffType.currentIndex()
        if staffType in (0, 2):
            # create a normal staff
            staff = ly.dom.Staff()
            seq = ly.dom.Seqr(staff)
            if self.clef:
                ly.dom.Clef(self.clef, seq)
            mus = ly.dom.Simr(seq)
            for a in assignments[:-1]:
                ly.dom.Identifier(a.name, mus)
                ly.dom.VoiceSeparator(mus)
            ly.dom.Identifier(assignments[-1].name, mus)
            builder.setMidiInstrument(staff, self.midiInstrument)

        if staffType in (1, 2):
            # create a tab staff
            tabstaff = ly.dom.TabStaff()
            if self.tabFormat:
                tabstaff.getWith()['tablatureFormat'] = ly.dom.Scheme(self.tabFormat)
            self.setTunings(tabstaff)
            sim = ly.dom.Simr(tabstaff)
            if numVoices == 1:
                ly.dom.Identifier(assignments[0].name, sim)
            else:
                for num, a in zip(order, assignments):
                    s = ly.dom.Seq(ly.dom.TabVoice(parent=sim))
                    ly.dom.Text('\\voice' + ly.util.int2text(num), s)
                    ly.dom.Identifier(a.name, s)

        if staffType == 0:
            # only a normal staff
            p = staff
        elif staffType == 1:
            # only a TabStaff
            builder.setMidiInstrument(tabstaff, self.midiInstrument)
            p = tabstaff
        else:
            # both TabStaff and normal staff
            p = ly.dom.StaffGroup()
            s = ly.dom.Sim(p)
            s.append(staff)
            s.append(tabstaff)

        builder.setInstrumentNamesFromPart(p, self, data)
        data.nodes.append(p)

    def setTunings(self, tab):
        if self.tunings:
            i = self.tuning.currentIndex()
            if i == 0:
                return
            elif i > len(self.tunings):
                value = ly.dom.Text("\\stringTuning <{0}>".format(self.customTuning.text()))
            else:
                tuning = self.tunings[self.tuning.currentIndex() - 1][0]
                value = ly.dom.Scheme(tuning)
            tab.getWith()['stringTunings'] = value


tablatureStaffTypes = (
    lambda: _("Normal staff"),
    lambda: _("Tablature"),
    #L10N: Both a Normal and a Tablature staff
    lambda: _("Both"),
)


class Mandolin(TablaturePart):
    @staticmethod
    def title(_=_base.translate):
        return _("Mandolin")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Mandolin", "Mdl.")

    midiInstrument = 'acoustic guitar (steel)'
    tunings = (
        ('mandolin-tuning', lambda: _("Mandolin tuning")),
    )


class Ukulele(TablaturePart):
    @staticmethod
    def title(_=_base.translate):
        return _("Ukulele")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Ukulele", "Uk.")

    midiInstrument = 'acoustic guitar (steel)'
    tunings = (
        ('ukulele-tuning', lambda: _("Ukulele tuning")),
        ('ukulele-d-tuning', lambda: _("Ukulele D-tuning")),
        ('tenor-ukulele-tuning', lambda: _("Tenor Ukulele tuning")),
        ('baritone-ukulele-tuning', lambda: _("Baritone Ukulele tuning")),
    )


class Banjo(TablaturePart):
    @staticmethod
    def title(_=_base.translate):
        return _("Banjo")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Banjo", "Bj.")

    midiInstrument = 'banjo'
    tabFormat = 'fret-number-tablature-format-banjo'
    tunings = (
        ('banjo-open-g-tuning', lambda: _("Open G-tuning (aDGBD)")),
        ('banjo-c-tuning', lambda: _("C-tuning (gCGBD)")),
        ('banjo-modal-tuning', lambda: _("Modal tuning (gDGCD)")),
        ('banjo-open-d-tuning', lambda: _("Open D-tuning (aDF#AD)")),
        ('banjo-open-dm-tuning', lambda: _("Open Dm-tuning (aDFAD)")),
    )

    def createTuningWidgets(self, layout):
        super(Banjo, self).createTuningWidgets(layout)
        self.fourStrings = QCheckBox()
        layout.addWidget(self.fourStrings)

    def translateTuningWidgets(self):
        super(Banjo, self).translateTuningWidgets()
        self.fourStrings.setText(_("Four strings (instead of five)"))

    def setTunings(self, tab):
        i = self.tuning.currentIndex()
        if i > len(self.tunings) or not self.fourStrings.isChecked():
            super(Banjo, self).setTunings(tab)
        else:
            tab.getWith()['stringTunings'] = ly.dom.Scheme(
                '(four-string-banjo {0})'.format(
                    self.tunings[i][0]))

    def slotCustomTuningEnable(self, index):
        super(Banjo, self).slotCustomTuningEnable(index)
        self.fourStrings.setEnabled(index <= len(self.tunings))


class ClassicalGuitar(TablaturePart):
    @staticmethod
    def title(_=_base.translate):
        return _("Classical guitar")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Classical guitar", "Gt.")

    midiInstrument = 'acoustic guitar (nylon)'
    clef = "treble_8"
    tunings = (
        ('guitar-tuning', lambda: _("Guitar tuning")),
        ('guitar-seven-string-tuning', lambda: _("Guitar seven-string tuning")),
        ('guitar-drop-d-tuning', lambda: _("Guitar drop-D tuning")),
        ('guitar-drop-c-tuning', lambda: _("Guitar drop-C tuning")),
        ('guitar-open-g-tuning', lambda: _("Open G-tuning")),
        ('guitar-open-d-tuning', lambda: _("Guitar open D tuning")),
        ('guitar-dadgad-tuning', lambda: _("Guitar d-a-d-g-a-d tuning")),
        ('guitar-lute-tuning', lambda: _("Lute tuning")),
        ('guitar-asus4-tuning', lambda: _("Guitar A-sus4 tuning")),
    )
    def createWidgets(self, layout):
        super(ClassicalGuitar, self).createWidgets(layout)
        self.voicesLabel = QLabel()
        self.voices = QSpinBox(minimum=1, maximum=4, value=1)
        box = QHBoxLayout()
        box.addWidget(self.voicesLabel)
        box.addWidget(self.voices)
        layout.addLayout(box)

    def translateWidgets(self):
        super(ClassicalGuitar, self).translateWidgets()
        self.voicesLabel.setText(_("Voices:"))

    def voiceCount(self):
        return self.voices.value()


class JazzGuitar(ClassicalGuitar):
    @staticmethod
    def title(_=_base.translate):
        return _("Jazz guitar")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Jazz guitar", "J.Gt.")

    midiInstrument = 'electric guitar (jazz)'


class Bass(TablaturePart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bass")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bass", "Bs.") #FIXME

    midiInstrument = 'acoustic bass'
    clef = 'bass_8'
    octave = -2
    tunings = (
        ('bass-tuning', lambda: _("Bass tuning")),
        ('bass-four-string-tuning', lambda: _("Four-string bass tuning")),
        ('bass-drop-d-tuning', lambda: _("Bass drop-D tuning")),
        ('bass-five-string-tuning', lambda: _("Five-string bass tuning")),
        ('bass-six-string-tuning', lambda: _("Six-string bass tuning")),
    )


class ElectricBass(Bass):
    @staticmethod
    def title(_=_base.translate):
        return _("Electric bass")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Electric bass", "E.Bs.")

    midiInstrument = 'electric bass (finger)'


class Harp(_base.PianoStaffPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Harp")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Harp", "Hp.")

    midiInstrument = 'orchestral harp'

    def translateWidgets(self):
        super(Harp, self).translateWidgets()
        self.upperVoicesLabel.setText(_("Upper staff:"))
        self.lowerVoicesLabel.setText(_("Lower staff:"))

    def build(self, data, builder):
        p = ly.dom.PianoStaff()
        builder.setInstrumentNamesFromPart(p, self, data)
        s = ly.dom.Sim(p)
        # add two staves, with a respective number of voices.
        self.buildStaff(data, builder, 'upper', 1, self.upperVoices.value(), s)
        self.buildStaff(data, builder, 'lower', 0, self.lowerVoices.value(), s, "bass")
        data.nodes.append(p)





register(
    lambda: _("Plucked strings"),
    [
        Mandolin,
        Banjo,
        Ukulele,
        ClassicalGuitar,
        JazzGuitar,
        Bass,
        ElectricBass,
        Harp,
    ])

