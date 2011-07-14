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
The score settings widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app

from . import scoreproperties

class SettingsWidget(QWidget):
   def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.scoreProperties = ScoreProperties()
        self.generalPreferences = GeneralPreferences()
        
        grid.addWidget(self.scoreProperties, 0, 0)
        grid.addWidget(self.generalPreferences, 0, 1)


class ScoreProperties(QGroupBox, scoreproperties.ScoreProperties):
    def __init__(self, parent = None):
        super(ScoreProperties, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.createWidgets()
        self.layoutWidgets(layout)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.translateWidgets()
        self.setTitle(_("Score properties"))
    


class GeneralPreferences(QGroupBox):
    def __init__(self, parent = None):
        super(GeneralPreferences, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.typq = QCheckBox()
        self.tagl = QCheckBox()
        self.barnum = QCheckBox()
        self.midi = QCheckBox()
        self.metro = QCheckBox()
        self.paperSizeLabel = QLabel()
        self.paper = QComboBox()
        self.paper.addItems(paperSizes)
        self.paperLandscape = QCheckBox(enabled=False)
        self.paper.activated.connect(self.slotPaperChanged)
        
        layout.addWidget(self.typq)
        layout.addWidget(self.tagl)
        layout.addWidget(self.barnum)
        layout.addWidget(self.midi)
        layout.addWidget(self.metro)
        
        box = QHBoxLayout(spacing=2)
        box.addWidget(self.paperSizeLabel)
        box.addWidget(self.paper)
        box.addWidget(self.paperLandscape)
        layout.addLayout(box)
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("General preferences"))
        self.typq.setText(_("Use typographical quotes"))
        self.typq.setToolTip(_(
            "Replace normal quotes in titles with nice typographical quotes."))
        self.tagl.setText(_("Remove default tagline"))
        self.tagl.setToolTip(_(
            "Suppress the default tagline output by LilyPond."))
        self.barnum.setText(_("Remove bar numbers"))
        self.barnum.setToolTip(_(
            "Suppress the display of measure numbers at the beginning of "
            "every system."))
        self.midi.setText(_("Create MIDI output"))
        self.midi.setToolTip(_(
            "Create a MIDI file in addition to the PDF file."))
        self.metro.setText(_("Show metronome mark"))
        self.metro.setToolTip(_(
            "If checked, show the metronome mark at the beginning of the "
            "score. The MIDI output also uses the metronome setting."))
        # paper size:
        self.paperSizeLabel.setText(_("Paper size:"))
        self.paper.setItemText(0, _("Default"))
        self.paperLandscape.setText(_("Landscape"))
  
    def slotPaperChanged(self, index):
        self.paperLandscape.setEnabled(bool(index))



paperSizes = ['', 'a3', 'a4', 'a5', 'a6', 'a7', 'legal', 'letter', '11x17']
