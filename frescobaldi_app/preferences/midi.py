# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright 2011 by Wilbert Berendsen
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
MIDI preferences.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *


import app
import util
import icons
import preferences
import midihub
import listmodel


class MidiPrefs(preferences.GroupsPage):
    def __init__(self, dialog):
        super(MidiPrefs, self).__init__(dialog)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(MidiPorts(self))
        layout.addWidget(Prefs(self))
        layout.addStretch(0)
    
    def saveSettings(self):
        super(MidiPrefs, self).saveSettings()
        midihub.settingsChanged()


class MidiPorts(preferences.Group):
    def __init__(self, page):
        super(MidiPorts, self).__init__(page)
        
        self._portsMessage = QLabel(wordWrap=True)
        self._playerLabel = QLabel()
        self._playerPort = QComboBox(editable=True,
            editTextChanged=self.changed, insertPolicy=QComboBox.NoInsert)
        
        self._reloadMidi = QPushButton(icon=icons.get('view-refresh'))
        self._reloadMidi.clicked.connect(self.refreshMidiPorts)
        
        grid = QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self._portsMessage, 0, 0, 1, 3)
        grid.addWidget(self._playerLabel, 1, 0)
        grid.addWidget(self._playerPort, 1, 1, 1, 2)
        grid.addWidget(self._reloadMidi, 2, 2)
        
        app.translateUI(self)
        self.loadMidiPorts()
    
    def translateUI(self):
        self.setTitle(_("MIDI Ports"))
        self._portsMessage.setText(_(
            "Note: There are no MIDI output ports available on your system. "
            "To use MIDI, please check if PortMIDI is installed on your system "
            "and that a MIDI synthesizer is available or connected."))
        self._playerLabel.setText(_("Player output:"))
        self._reloadMidi.setText(_("Refresh MIDI ports"))

    def loadMidiPorts(self):
        output = midihub.output_ports()
        self._playerPort.setModel(listmodel.ListModel(output))
        self._portsMessage.setVisible(not output)

    def refreshMidiPorts(self):
        midihub.refresh_ports()
        with util.signalsBlocked(self):
            self.loadMidiPorts()
            self.loadSettings()

    def loadSettings(self):
        port = midihub.default_output()
        s = QSettings()
        s.beginGroup("midi")
        self._playerPort.setEditText(s.value("player/output_port", port))
        
    def saveSettings(self):
        s = QSettings()
        s.beginGroup("midi")
        s.setValue("player/output_port", self._playerPort.currentText())


class Prefs(preferences.Group):
    def __init__(self, page):
        super(Prefs, self).__init__(page)
        
        self._closeOutputs = QCheckBox()
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(self._closeOutputs)
        app.translateUI(self)
    
    def translateUI(self):
        self.setTitle(_("Preferences"))
        self._closeOutputs.setText(_("Close unused MIDI output"))
        self._closeOutputs.setToolTip(_(
            "Closes unused MIDI ports after one minute. "
            "See \"What's This\" for more information."))
        self._closeOutputs.setWhatsThis(_(
            "<p>If checked, Frescobaldi will close MIDI output ports that are not "
            "used for one minute.</p>\n"
            "<p>This could free up system resources that a software MIDI synthesizer "
            "might be using, thus saving battery power.</p>\n"
            "<p>A side effect is that if you pause a MIDI file for a long time "
            "the instruments are reset to the default piano (instrument 0). "
            "In that case, playing the file from the beginning sets up the "
            "instruments again.</p>\n"))

    def loadSettings(self):
        self._closeOutputs.setChecked(
            QSettings().value("midi/close_outputs", False) in (True, 'true'))
    
    def saveSettings(self):
        QSettings().setValue("midi/close_outputs", self._closeOutputs.isChecked())



