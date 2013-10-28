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
The preview options widget.
"""

from __future__ import unicode_literals

import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import preview_mode


class Widget(QWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool)
        
        layout = QVBoxLayout(spacing=1)
        self.setLayout(layout)
        
        # automatically processed modes
        self.checkboxes = {}
        for mode in preview_mode.modelist():
            self.checkboxes[mode] = cb = QCheckBox()
            cb.toggled.connect(self.toggleOption)
            layout.addWidget(cb)
        
        # manual mode UI elements that need special treatment
        self.CBdisablepointandclick = QCheckBox()
        self.CBcustomfile = QCheckBox()
        self.LEcustomfile = QLineEdit(enabled=False)
        
        # add manual widgets
        layout.addWidget(self.CBdisablepointandclick)
        layout.addWidget(self.CBcustomfile)
        layout.addWidget(self.LEcustomfile)
        layout.addStretch(1)
        
        # connect manual widgets
        self.CBdisablepointandclick.toggled.connect(self.togglePointAndClick)
        self.CBcustomfile.toggled.connect(self.toggleCustomFile)
        self.LEcustomfile.textEdited.connect(self.customFileEdited)
        
        app.translateUI(self)
        self.loadSettings()
    
    def translateUI(self):
        for mode in preview_mode.modelist():
            label = preview_mode.label(mode)
            tooltip = preview_mode.tooltip(mode)
            self.checkboxes[mode].setText(label)
            self.checkboxes[mode].setToolTip(tooltip)
        
        self.CBdisablepointandclick.setText(_("Disable Point-and-Click"))
        self.CBcustomfile.setText(_("Include Custom File:"))
        self.CBcustomfile.setToolTip(_("Include a custom file with definitions\n"
                      "for additional Debug Modes"))
        self.LEcustomfile.setToolTip(_(
       
            "Filename to be included"))
    def loadSettings(self):
        """Called on construction. Load settings and set checkboxes state."""
        s = QSettings()
        s.beginGroup('lilypond_settings')
        for mode in preview_mode.modelist():
            
            self.checkboxes[mode].setChecked(s.value(mode, False, bool))
        
        self.LEcustomfile.setText(s.value('custom-filename', '', type("")))
        
    def customFileEdited(self):
        """Called when the user types in the custom file entry."""
        s = QSettings()
        s.beginGroup("lilypond_settings")
        s.setValue("custom-filename", self.LEcustomfile.text())

    def toggleOption(self, state):
        """Called when a checkbox is toggled by the user."""
        for mode in preview_mode.modelist():
            if self.checkboxes[mode] == self.sender():
                s = QSettings()
                s.beginGroup("lilypond_settings")
                s.setValue(mode, state)
                break

    def toggleCustomFile(self, state):
        """Called when the custom file checkbox is toggled"""
        s = QSettings()
        s.beginGroup("lilypond_settings")
        s.setValue('custom-file', state)
        self.LEcustomfile.setEnabled(state)

    def togglePointAndClick(self, state):
        s = QSettings()
        s.beginGroup("lilypond_settings")
        s.setValue('disable-point-and-click', state)

