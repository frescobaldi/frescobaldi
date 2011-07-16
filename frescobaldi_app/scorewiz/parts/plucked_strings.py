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
Plucked string part types.
"""

import __builtin__

from PyQt4.QtGui import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QSpinBox

import listmodel

from . import _base
from . import register


class TablaturePart(_base.Part):
    """Base class for tablature instrument part types."""
    
    octave = 0
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
        self.tuning.setModel(listmodel.ListModel(tunings, self.tuning,
            display=listmodel.translate_index(1)))
        self.tuning.setCurrentIndex(1)
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.tuningLabel)
        box.addWidget(self.tuning)
    
    def translateWidgets(self):
        self.staffTypeLabel.setText(_("Staff type:"))
        self.staffType.model().update()
        if self.tunings:
            self.translateTuningWidgets()
    
    def translateTuningWidgets(self):
        self.tuningLabel.setText(_("Tuning:"))
        self.tuning.model().update()
    
    def slotTabEnable(self, enable):
        """Called when the user changes the staff type.
        
        Non-zero if the user wants a TabStaff.
        
        """
        self.tuning.setEnabled(bool(enable))
        
        
tablatureStaffTypes = (
    lambda: _("Normal staff"),
    lambda: _("Tablature"),
    #L10N: Both a Normal and a Tablature staff
    lambda: _("Both"),
)


class Mandolin(TablaturePart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Mandolin")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Mandolin", "Mdl.")
    
    midiInstrument = 'acoustic guitar (steel)'
    tunings = (
        ('mandolin-tuning', lambda: _("Mandolin tuning")),
    )
    

class Banjo(TablaturePart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Banjo")
    
    @staticmethod
    def short(_=__builtin__._):
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


class ClassicalGuitar(TablaturePart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Classical guitar")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Classical guitar", "Gt.")
    
    midiInstrument = 'acoustic guitar (nylon)'
    clef = "treble_8"
    tunings = (
        ('guitar-tuning', lambda: _("Guitar tuning")),
        ('guitar-open-g-tuning', lambda: _("Open G-tuning")),
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


class JazzGuitar(ClassicalGuitar):
    @staticmethod
    def title(_=__builtin__._):
        return _("Jazz guitar")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Jazz guitar", "J.Gt.")
    
    midiInstrument = 'electric guitar (jazz)'


class Bass(TablaturePart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Bass")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Bass", "Bs.") #FIXME

    midiInstrument = 'acoustic bass'
    clef = 'bass_8'
    octave = -2
    tunings = (
        ('bass-tuning', lambda: _("Bass tuning")),
    )


class ElectricBass(Bass):
    @staticmethod
    def title(_=__builtin__._):
        return _("Electric bass")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Electric bass", "E.Bs.")

    midiInstrument = 'electric bass (finger)'


class Harp(_base.Part):
    @staticmethod
    def title(_=__builtin__._):
        return _("Harp")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Harp", "Hp.")

    midiInstrument = 'harp'

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
        self.upperVoicesLabel.setText(_("Upper staff:"))
        self.lowerVoicesLabel.setText(_("Lower staff:"))
        



register(
    lambda: _("Plucked strings"),
    [
        Mandolin,
        Banjo,
        ClassicalGuitar,
        JazzGuitar,
        Bass,
        ElectricBass,
        Harp,
    ])

