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


