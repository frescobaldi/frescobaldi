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
Import Midi dialog.
Uses midi2ly to create ly file from midi.
In the dialog the options of midi2ly can be set.
"""


from PyQt5.QtCore import QSettings, QSize
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialogButtonBox, QLabel)

import app
import qutil

from . import toly_dialog



class Dialog(toly_dialog.ToLyDialog):

    def __init__(self, parent=None):

        self.imp_prgm = "midi2ly"
        self.userg = "midi_import"

        self.useAbsCheck = QCheckBox()

        self.impChecks = [self.useAbsCheck]

        self.useAbsCheck.setObjectName("absolute-mode")

        self.impExtra = []

        super(Dialog, self).__init__(parent)

        app.translateUI(self)
        qutil.saveDialogSize(self, "midi_import/dialog/size", QSize(480, 260))

        self.makeCommandLine()

        self.loadSettings()

    def translateUI(self):
        self.useAbsCheck.setText(_("Pitches in absolute mode"))

        self.buttons.button(QDialogButtonBox.Ok).setText(_("Run midi2ly"))

        super(Dialog, self).translateUI()

    def makeCommandLine(self):
        """Reads the widgets and builds a command line."""
        cmd = ["$midi2ly"]
        if self.useAbsCheck.isChecked():
            cmd.append('-a')

        cmd.append("$filename")
        self.commandLine.setText(' '.join(cmd))

    def loadSettings(self):
        """Get users previous settings."""
        self.imp_default = [False]
        self.settings = QSettings()
        self.settings.beginGroup('midi_import')
        super(Dialog, self).loadSettings()

    def saveSettings(self):
        """Save users last settings."""
        self.settings = QSettings()
        self.settings.beginGroup('midi_import')
        super(Dialog, self).saveSettings()
