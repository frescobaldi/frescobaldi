# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Export settings dialog.
"""

from __future__ import unicode_literals

import collections
import os

from PyQt4.QtCore import QSettings, QSize, Qt, QUrl
from PyQt4.QtGui import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QTextEdit)
from PyQt4.QtGui import (
    QDialog, QDialogButtonBox, QLabel, QLayout, QTabWidget, QTextBrowser,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton)

import app
import help
import icons
import qutil

import widgets
import info
import export


class ExportDialog(QDialog):
    """A dialog to define source code export settings.
    
    Tries to be as strict about interdepending properties.
    Optionally saves to Preferences.
    # autosave if enabled
    
    """
    def __init__(self, mainwindow):
        """Creates the about dialog. exec_() returns True or False."""
        super(ExportDialog, self).__init__(mainwindow)
        
        self.setWindowTitle(_("Export Source As..."))
        layout = QVBoxLayout()
        grid = QGridLayout()
        btn = QHBoxLayout()
        self.setLayout(layout)
        
        self.autoSave = QCheckBox()
        self.autoSave.setText(_("Remember settings for source code export."))
        self.autoSave.setToolTip(_(
            "If checked, Frescobaldi will keep settings for source code "
            "export throughout sessions, without explicitely saving them."))

        grid.addWidget(self.autoSave, 0, 0)
        
        self.save = QPushButton("Save settings")
        btn.addWidget(self.save)
        
        b = self.buttons = QDialogButtonBox(self)
        b.setStandardButtons(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel)
        btn.addWidget(b)
        
        layout.addLayout(grid)
        layout.addLayout(btn)
        
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        self.save.clicked.connect(self.saveSettings)
        
        
    def load_settings(self):
        s = QSettings()
        s.beginGroup("export")
        self.autoSave.setChecked(s.value("autosave_settings", True, bool))
        
    def saveSettings(self):
        print export.options._options
        print "1", export.options.changed()
        export.options.save()
        self.updateLogic()
        
    def updateLogic(self):
        print "2", export.options.changed()
        self.save.setEnabled(export.options.changed())
        
    def translateUI(self):
        self.setTitle(_("Export Source As..."))
        self.autoSave.setText(_("Remember settings for source code export."))
        self.autoSave.setToolTip(_(
            "If checked, Frescobaldi will keep settings for source code "
            "export throughout sessions, without explicitely saving them."))

        

