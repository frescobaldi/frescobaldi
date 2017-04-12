# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QVBoxLayout)


import app
import qutil
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
        self._inputLabel = QLabel()
        self._inputPort = QComboBox(editable=True,
            editTextChanged=self.changed, insertPolicy=QComboBox.NoInsert)

        self._reloadMidi = QPushButton(icon=icons.get('view-refresh'))
        self._reloadMidi.clicked.connect(self.refreshMidiPorts)

        grid = QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self._portsMessage, 0, 0, 1, 3)
        grid.addWidget(self._playerLabel, 1, 0)
        grid.addWidget(self._playerPort, 1, 1, 1, 2)
        grid.addWidget(self._inputLabel, 2, 0)
        grid.addWidget(self._inputPort, 2, 1, 1, 2)
        grid.addWidget(self._reloadMidi, 3, 2)

        app.translateUI(self)
        self.loadMidiPorts()

    def translateUI(self):
        self.setTitle(_("MIDI Ports"))
        self._portsMessage.setText(_(
            "Note: There are no MIDI output ports available on your system. "
            "To use MIDI, please check if PortMIDI is installed on your system "
            "and that a MIDI synthesizer is available or connected."))
        self._playerLabel.setText(_("Player output:"))
        self._playerPort.setToolTip(_(
            "The MIDI port to play music to. "
            "See \"What's This\" for more information."))
        self._playerPort.setWhatsThis(_(
            "<p>"
            "This dropdown menu lists the available MIDI output ports on your system. "
            "You can select one, or just type part of a name. "
            "In that case, the first available port name that starts with the "
            "specified characters is used."
            "</p>\n<p>"
            "Click the button to refresh the list, e.g. when you connect a "
            "MIDI device or start a software synthesizer."
            "</p>"))
        self._inputLabel.setText(_("Input port:"))
        self._inputPort.setToolTip(_(
            "The MIDI port to get input from to write notes  "
            "See \"What's This\" for more information."))
        self._inputPort.setWhatsThis(_(
            "<p>"
            "This dropdown menu lists the available MIDI input ports on your system. "
            "You can select one, or just type part of a name. "
            "In that case, the first available port name that starts with the "
            "specified characters is used."
            "</p>\n<p>"
            "Click the button to refresh the list, e.g. when you connect a "
            "MIDI device or start a software synthesizer."
            "</p>"))
        self._reloadMidi.setText(_("Refresh MIDI ports"))

    def loadMidiPorts(self):
        output_ports = midihub.output_ports()
        self._playerPort.setModel(listmodel.ListModel(output_ports))
        input_ports = midihub.input_ports()
        self._inputPort.setModel(listmodel.ListModel(input_ports))
        self._portsMessage.setVisible((not output_ports) and (not input_ports))

    def refreshMidiPorts(self):
        midihub.refresh_ports()
        with qutil.signalsBlocked(self):
            self.loadMidiPorts()
            self.loadSettings()

    def loadSettings(self):
        output_port = midihub.default_output()
        input_port = midihub.default_input()
        s = QSettings()
        s.beginGroup("midi")
        self._playerPort.setEditText(s.value("player/output_port", output_port, str))
        self._inputPort.setEditText(s.value("midi/input_port", input_port, str))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("midi")
        s.setValue("player/output_port", self._playerPort.currentText())
        s.setValue("midi/input_port", self._inputPort.currentText())


class Prefs(preferences.Group):
    def __init__(self, page):
        super(Prefs, self).__init__(page)

        self._closeOutputs = QCheckBox(clicked=self.changed)
        self._pollingLabel = QLabel()
        self._pollingTime = QSpinBox()
        self._pollingTime.setRange(0, 1000)
        self._pollingTime.setSuffix(" ms")
        self._pollingTime.valueChanged.connect(self.changed)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self._closeOutputs)
        app.translateUI(self)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        hbox.addWidget(self._pollingLabel)
        hbox.addWidget(self._pollingTime)

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
        self._pollingLabel.setText(_("Polling time for input:"))
        self._pollingTime.setToolTip(_(
            "Polling time for MIDI input. "
            "See \"What's This\" for more information."))
        self._pollingTime.setWhatsThis(_(
            "Sets the time between the polling of the MIDI input port in milliseconds. "
            "Small values lead to faster recognition of incoming MIDI events, but stress "
            "the CPU. 10 ms should be a good value."))

    def loadSettings(self):
        s = QSettings()
        self._closeOutputs.setChecked(
            s.value("midi/close_outputs", False, bool))
        self._pollingTime.setValue(
            s.value("midi/polling_time", 10, int))

    def saveSettings(self):
        s = QSettings()
        s.setValue("midi/close_outputs", self._closeOutputs.isChecked())
        s.setValue("midi/polling_time", self._pollingTime.value())
