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
Import ABC dialog.
Uses abc2ly to create ly file from abc.
In the dialog the options of abc2ly can be set.
"""


import os
import subprocess
import sys

from PyQt5.QtCore import QSettings, QSize
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialogButtonBox, QLabel)

import app
import util
import qutil

from . import toly_dialog


class Dialog(toly_dialog.ToLyDialog):

    def __init__(self, parent=None):

        self.imp_prgm = "abc2ly"
        self.userg = "abc_import"

        self.nobeamCheck = QCheckBox()

        self.impChecks = [self.nobeamCheck]

        self.nobeamCheck.setObjectName("import-beaming")

        self.impExtra = []

        super(Dialog, self).__init__(parent)

        app.translateUI(self)
        qutil.saveDialogSize(self, "abc_import/dialog/size", QSize(480, 160))

        self.makeCommandLine()

        self.loadSettings()

    def translateUI(self):
        self.nobeamCheck.setText(_("Import beaming"))

        self.buttons.button(QDialogButtonBox.Ok).setText(_("Run abc2ly"))

        super(Dialog, self).translateUI()

    def makeCommandLine(self):
        """Reads the widgets and builds a command line."""
        cmd = ["$abc2ly"]
        if self.nobeamCheck.isChecked():
            cmd.append('-b')

        cmd.append("$filename")
        self.commandLine.setText(' '.join(cmd))

    def run_command(self):
        """ABC import (at least for now) needs a specific solution here."""
        cmd = self.getCmd('document.ly')
        directory = util.tempdir()
        subenviron = None
        if os.name == "nt":
            # Python 2.7 subprocess on Windows chokes on unicode in env
            subenviron = util.bytes_environ()
        else:
            subenviron = dict(os.environ)
        if sys.platform.startswith('darwin'):
            try:
                del subenviron['PYTHONHOME']
            except KeyError:
                pass
            try:
                del subenviron['PYTHONPATH']
            except KeyError:
                pass
        proc = subprocess.Popen(cmd, cwd=directory,
            env = subenviron,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
        stdouterr = proc.communicate()
        if not stdouterr[0]:
            try:
                with open(os.path.join(directory, cmd[-1])) as abc:
                    stdouterr = (abc.read(), stdouterr[1])
            except IOError:
                pass
        return stdouterr

    def loadSettings(self):
        """Get users previous settings."""
        self.imp_default = [True]
        self.settings = QSettings()
        self.settings.beginGroup('abc_import')
        super(Dialog, self).loadSettings()

    def saveSettings(self):
        """Save users last settings."""
        self.settings = QSettings()
        self.settings.beginGroup('abc_import')
        super(Dialog, self).saveSettings()
