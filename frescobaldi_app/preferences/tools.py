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
Per-tool preferences.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import (
    QCheckBox, QDoubleSpinBox, QFont, QFontComboBox, QHBoxLayout, QLabel, QVBoxLayout)

import app
import util
import preferences


class Tools(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Tools, self).__init__(dialog)

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(LogTool(self))
        layout.addStretch(1)
            

class LogTool(preferences.Group):
    def __init__(self, page):
        super(LogTool, self).__init__(page)
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fontLabel = QLabel()
        self.fontChooser = QFontComboBox(currentFontChanged=self.changed)
        self.fontSize = QDoubleSpinBox(valueChanged=self.changed)
        self.fontSize.setRange(6.0, 32.0)
        self.fontSize.setSingleStep(0.5)
        self.fontSize.setDecimals(1)

        box = QHBoxLayout()
        box.addWidget(self.fontLabel)
        box.addWidget(self.fontChooser, 1)
        box.addWidget(self.fontSize)
        layout.addLayout(box)
        
        self.showlog = QCheckBox(toggled=self.changed)
        layout.addWidget(self.showlog)
        
        self.rawview = QCheckBox(toggled=self.changed)
        layout.addWidget(self.rawview)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("LilyPond Log"))
        self.fontLabel.setText(_("Font:"))
        self.showlog.setText(_("Show log when a job is started"))
        self.rawview.setText(_("Display plain log output"))
        self.rawview.setToolTip(_(
            "If checked, Frescobaldi will not shorten filenames in the log output."""))
    
    def loadSettings(self):
        s = QSettings()
        s.beginGroup("log")
        font = QFont(s.value("fontfamily", "monospace"))
        font.setPointSizeF(float(s.value("fontsize", 9.0)))
        with util.signalsBlocked(self.fontChooser, self.fontSize):
            self.fontChooser.setCurrentFont(font)
            self.fontSize.setValue(font.pointSizeF())
        self.showlog.setChecked(s.value("show_on_start", True) not in (False, "false"))
        self.rawview.setChecked(s.value("rawview", True) not in (False, "false"))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("log")
        s.setValue("fontfamily", self.fontChooser.currentFont().family())
        s.setValue("fontsize", self.fontSize.value())
        s.setValue("show_on_start", self.showlog.isChecked())
        s.setValue("rawview", self.rawview.isChecked())


