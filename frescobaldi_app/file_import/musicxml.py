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
Import Music XML dialog.
Uses musicxml2ly to create ly file from xml.
In the dialog the options of musicxml2ly can be set.
"""


from PyQt5.QtCore import QSettings, QSize
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialogButtonBox, QLabel)

import app
import qutil

from . import toly_dialog

# language names musicxml2ly allows
_langlist = [
    'nederlands',
    'catalan',
    'deutsch',
    'english',
    'espanol',
    'italiano',
    'norsk',
    'portugues',
    'suomi',
    'svenska',
    'vlaams',
]


class Dialog(toly_dialog.ToLyDialog):

    def __init__(self, parent=None):

        self.imp_prgm = "musicxml2ly"
        self.userg = "musicxml_import"

        self.noartCheck = QCheckBox()
        self.norestCheck = QCheckBox()
        self.nolayoutCheck = QCheckBox()
        self.nobeamCheck = QCheckBox()
        self.useAbsCheck = QCheckBox()
        self.commMidiCheck = QCheckBox()

        self.langCombo = QComboBox()
        self.langLabel = QLabel()

        self.impChecks = [self.noartCheck,
                          self.norestCheck,
                          self.nolayoutCheck,
                          self.nobeamCheck,
                          self.useAbsCheck,
                          self.commMidiCheck]

        self.noartCheck.setObjectName("articulation-directions")
        self.norestCheck.setObjectName("rest-positions")
        self.nolayoutCheck.setObjectName("page-layout")
        self.nobeamCheck.setObjectName("import-beaming")
        self.useAbsCheck.setObjectName("absolute-mode")
        self.commMidiCheck.setObjectName("comment-out-midi")

        self.langCombo.addItem('')
        self.langCombo.addItems(_langlist)

        self.impExtra = [self.langLabel, self.langCombo]

        super(Dialog, self).__init__(parent)

        self.langCombo.currentIndexChanged.connect(self.makeCommandLine)
        app.translateUI(self)
        qutil.saveDialogSize(self, "musicxml_import/dialog/size", QSize(480, 260))

        self.makeCommandLine()

        self.loadSettings()

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Import Music XML")))
        self.noartCheck.setText(_("Import articulation directions"))
        self.norestCheck.setText(_("Import rest positions"))
        self.nolayoutCheck.setText(_("Import page layout"))
        self.nobeamCheck.setText(_("Import beaming"))
        self.useAbsCheck.setText(_("Pitches in absolute mode"))
        self.commMidiCheck.setText(_("Comment out midi block"))

        self.langLabel.setText(_("Language for pitch names"))
        self.langCombo.setItemText(0, _("Default"))

        self.buttons.button(QDialogButtonBox.Ok).setText(_("Run musicxml2ly"))

        super(Dialog, self).translateUI()

    def makeCommandLine(self):
        """Reads the widgets and builds a command line."""
        cmd = ["$musicxml2ly"]
        if self.useAbsCheck.isChecked():
            cmd.append('-a')
        if not self.noartCheck.isChecked():
            cmd.append('--nd')
        if not self.norestCheck.isChecked():
            cmd.append('--nrp')
        if not self.nolayoutCheck.isChecked():
            cmd.append('--npl')
        if not self.nobeamCheck.isChecked():
            cmd.append('--no-beaming')
        if not self.commMidiCheck.isChecked():
            cmd.append('-m')
        index = self.langCombo.currentIndex()
        if index > 0:
            cmd.append('--language=' + _langlist[index - 1])

        cmd.append("$filename")
        self.commandLine.setText(' '.join(cmd))

    def loadSettings(self):
        """Get users previous settings."""
        self.imp_default = [False, False, False, False, False, False]
        self.settings = QSettings()
        self.settings.beginGroup('musicxml_import')
        super(Dialog, self).loadSettings()
        lang = self.settings.value("language", "default", str)
        try:
            index = _langlist.index(lang)
        except ValueError:
            index = -1
        self.langCombo.setCurrentIndex(index + 1)

    def saveSettings(self):
        """Save users last settings."""
        self.settings = QSettings()
        self.settings.beginGroup('musicxml_import')
        super(Dialog, self).saveSettings()
        index = self.langCombo.currentIndex()
        self.settings.setValue('language', 'default' if index == 0 else _langlist[index-1])
