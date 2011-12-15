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
Helper application preferences
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QGridLayout, QLabel, QVBoxLayout

import app
import util
import icons
import preferences
import widgets.lineedit


class Helpers(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Helpers, self).__init__(dialog)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(Apps(self))
        layout.addStretch(0)


class Apps(preferences.Group):
    def __init__(self, page):
        super(Apps, self).__init__(page)
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.pdfLabel = QLabel()
        self.pdfEntry = widgets.lineedit.LineEdit(textChanged=self.changed)
        self.midiLabel = QLabel()
        self.midiEntry = widgets.lineedit.LineEdit(textChanged=self.changed)
        self.svgLabel = QLabel()
        self.svgEntry = widgets.lineedit.LineEdit(textChanged=self.changed)
        self.browserLabel = QLabel()
        self.browserEntry = widgets.lineedit.LineEdit(textChanged=self.changed)
        self.emailLabel = QLabel()
        self.emailEntry = widgets.lineedit.LineEdit(textChanged=self.changed)
        self.directoryLabel = QLabel()
        self.directoryEntry = widgets.lineedit.LineEdit(textChanged=self.changed)
        self.terminalLabel = QLabel()
        self.terminalEntry = widgets.lineedit.LineEdit(textChanged=self.changed)
        
        layout.addWidget(self.pdfLabel, 0, 0)
        layout.addWidget(self.pdfEntry, 0, 1)
        layout.addWidget(self.midiLabel, 1, 0)
        layout.addWidget(self.midiEntry, 1, 1)
        layout.addWidget(self.svgLabel, 2, 0)
        layout.addWidget(self.svgEntry, 2, 1)
        layout.addWidget(self.browserLabel, 3, 0)
        layout.addWidget(self.browserEntry, 3, 1)
        layout.addWidget(self.emailLabel, 4, 0)
        layout.addWidget(self.emailEntry, 4, 1)
        layout.addWidget(self.directoryLabel, 5, 0)
        layout.addWidget(self.directoryEntry, 5, 1)
        layout.addWidget(self.terminalLabel, 6, 0)
        layout.addWidget(self.terminalEntry, 6, 1)
        
        app.translateUI(self)
    
    def translateUI(self):
        self.setTitle(_("Helper Applications"))
        self.pdfLabel.setText(_("PDF:"))
        self.midiLabel.setText(_("MIDI:"))
        self.svgLabel.setText(_("SVG:"))
        self.browserLabel.setText(_("Browser:"))
        self.emailLabel.setText(_("E-Mail:"))
        self.directoryLabel.setText(_("File Manager:"))
        self.terminalLabel.setText(_("Shell:"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("helper_applications")
        self.pdfEntry.setText(s.value("pdf", ""))
        self.midiEntry.setText(s.value("midi", ""))
        self.svgEntry.setText(s.value("svg", ""))
        self.browserEntry.setText(s.value("browser", ""))
        self.emailEntry.setText(s.value("email", ""))
        self.directoryEntry.setText(s.value("directory", ""))
        self.terminalEntry.setText(s.value("terminal", ""))
    
    def saveSettings(self):
        s= QSettings()
        s.beginGroup("helper_applications")
        s.setValue("pdf", self.pdfEntry.text())
        s.setValue("midi", self.midiEntry.text())
        s.setValue("svg", self.svgEntry.text())
        s.setValue("browser", self.browserEntry.text())
        s.setValue("email", self.emailEntry.text())
        s.setValue("directory", self.directoryEntry.text())
        s.setValue("terminal", self.terminalEntry.text())


