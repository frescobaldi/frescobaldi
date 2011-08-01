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
Keyboard part types.
"""

import __builtin__

from PyQt4.QtGui import QGridLayout, QLabel, QSpinBox

import ly.dom
import ly.util

from . import _base
from . import register


class KeyboardPart(_base.Part):
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
        """ setup structure for a 2-staff PianoStaff. """
        p = ly.dom.PianoStaff()
        builder.setInstrumentNamesFromPart(p, self, data)
        s = ly.dom.Sim(p)
        # add two staves, with a respective number of voices.
        self.buildStaff(data, builder, 'right', 1, self.upperVoices.value(), s)
        self.buildStaff(data, builder, 'left', 0, self.lowerVoices.value(), s, "bass")
        data.nodes.append(p)



class Piano(KeyboardPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Piano")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Piano", "Pno.")
    
    midiInstrument = 'acoustic grand'


class Harpsichord(KeyboardPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Harpsichord")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Harpsichord", "Hs.")
    
    midiInstrument = 'harpsichord'


class Clavichord(KeyboardPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Clavichord")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Clavichord", "Clv.")
    
    midiInstrument = 'clav'


class Organ(KeyboardPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Organ")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Organ", "Org.")
    
    midiInstrument = 'church organ'

    def createWidgets(self, layout):
        super(Organ, self).createWidgets(layout)
        grid = layout.itemAt(layout.count() - 1).layout()
        self.pedalVoices = QSpinBox(minimum=0, maximum=4, value=1)
        self.pedalVoicesLabel = QLabel()
        self.pedalVoicesLabel.setBuddy(self.pedalVoices)
        grid.addWidget(self.pedalVoicesLabel, 2, 0)
        grid.addWidget(self.pedalVoices)
        
    def translateWidgets(self):
        super(Organ, self).translateWidgets()
        self.pedalVoicesLabel.setText(_("Pedal:"))
        self.pedalVoices.setToolTip(_(
            "Set to 0 to disable the pedal altogether."))
    
    def build(self, data, builder):
        super(Organ, self).build(data, builder)
        if self.pedalVoices.value():
            data.nodes.append(self.buildStaff(data, builder,
                'pedal', -1, self.pedalVoices.value(), clef="bass"))



class Celesta(KeyboardPart):
    @staticmethod
    def title(_=__builtin__._):
        return _("Celesta")
    
    @staticmethod
    def short(_=__builtin__._):
        return _("abbreviation for Celesta", "Cel.")
    
    midiInstrument = 'celesta'


register(
    lambda: _("Keyboard instruments"),
    [
        Piano,
        Harpsichord,
        Clavichord,
        Organ,
        Celesta,
    ])


