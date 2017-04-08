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
The Layout Control options widget.
"""


import sys

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtWidgets import (QCheckBox, QHBoxLayout, QLineEdit, QToolButton,
                             QVBoxLayout, QWidget)

import app
import icons
import layoutcontrol
import engrave
import userguide


class Widget(QWidget):

    optionsChanged = pyqtSignal()

    def __init__(self, tool):
        super(Widget, self).__init__(tool)

        layout = QVBoxLayout(spacing=1)
        self.setLayout(layout)

        # manual mode UI elements that need special treatment
        self.CBverbose = QCheckBox(clicked=self.optionsChanged)
        self.CBpointandclick = QCheckBox(clicked=self.optionsChanged)
        self.CBcustomfile = QCheckBox(clicked=self.optionsChanged)
        self.LEcustomfile = QLineEdit(enabled=False)

        # run Lily button
        self.engraveButton = QToolButton()
        self.engraveButton.setDefaultAction(
            engrave.engraver(tool.mainwindow()).actionCollection.engrave_debug)

        # help button
        self.helpButton = QToolButton(clicked=self.helpButtonClicked)
        self.helpButton.setIcon(icons.get('help-contents'))

        # add manual widgets
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.engraveButton)
        hbox.addWidget(self.helpButton)
        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addWidget(self.CBverbose)
        layout.addWidget(self.CBpointandclick)

        # automatically processed modes
        self.checkboxes = {}
        for mode in layoutcontrol.modelist():
            self.checkboxes[mode] = cb = QCheckBox(clicked=self.optionsChanged)
            layout.addWidget(cb)

        # add manual widgets
        layout.addWidget(self.CBcustomfile)
        layout.addWidget(self.LEcustomfile)
        layout.addStretch(1)

        # connect manual widgets
        self.CBcustomfile.toggled.connect(self.LEcustomfile.setEnabled)
        self.LEcustomfile.textEdited.connect(self.optionsChanged)

        app.translateUI(self)
        self.loadSettings()
        tool.mainwindow().aboutToClose.connect(self.saveSettings)

    def translateUI(self):
        for mode in layoutcontrol.modelist():
            label = layoutcontrol.label(mode)
            tooltip = layoutcontrol.tooltip(mode)
            self.checkboxes[mode].setText(label)
            self.checkboxes[mode].setToolTip(tooltip)
        self.helpButton.setText(_("Help"))
        self.helpButton.setToolTip(_("Help"))
        self.CBverbose.setText(_("Verbose output"))
        self.CBverbose.setToolTip(_("Run LilyPond with verbose output"))
        self.CBpointandclick.setText(_("Point-and-Click"))
        self.CBpointandclick.setToolTip(_("Run LilyPond in preview mode (with Point and Click)"))
        self.CBcustomfile.setText(_("Include Custom File:"))
        self.CBcustomfile.setToolTip(_("Include a custom file with definitions\n"
                      "for additional Layout Control Modes"))
        self.LEcustomfile.setToolTip(_("Filename to be included"))

    def loadSettings(self):
        """Called on construction. Load settings and set checkboxes state."""
        s = QSettings()
        s.beginGroup('lilypond_settings')
        for mode in layoutcontrol.modelist():
            self.checkboxes[mode].setChecked(s.value(mode, False, bool))
        self.CBverbose.setChecked(s.value('verbose', False, bool))
        self.CBpointandclick.setChecked(s.value('point-and-click', True, bool))
        self.CBcustomfile.setChecked(s.value('custom-file', False, bool))
        self.LEcustomfile.setText(s.value('custom-filename', '', str))

    def saveSettings(self):
        """Called on close. Save settings and checkboxes state."""
        s = QSettings()
        s.beginGroup('lilypond_settings')
        for mode in layoutcontrol.modelist():
            s.setValue(mode, self.checkboxes[mode].isChecked())
        s.setValue('verbose', self.CBverbose.isChecked())
        s.setValue('point-and-click', self.CBpointandclick.isChecked())
        s.setValue('custom-file', self.CBcustomfile.isChecked())
        s.setValue('custom-filename', self.LEcustomfile.text())

    def helpButtonClicked(self):
        userguide.show("engrave_layout")

    def preview_options(self):
        """Return a list of Debug Mode command line options for LilyPond."""
        args = []

        # 'automatic' widgets
        for mode in layoutcontrol.modelist():
            if self.checkboxes[mode].isChecked():
                args.append(layoutcontrol.option(mode))

        # manual widgets
        if self.CBcustomfile.isChecked():
            file_to_include = self.LEcustomfile.text()
            args.append('-ddebug-custom-file=' + file_to_include)

        # if at least one debug mode is used, add the directory with the
        # preview-mode files to the search path
        if args:
            args.insert(0, '-I' + layoutcontrol.__path__[0])
            # File that conditionally includes different formatters
            args.insert(1, '-dinclude-settings=debug-layout-options.ly')

        if self.CBpointandclick.isChecked():
            args.insert(0, '-dpoint-and-click')
        else:
            args.insert(0, '-dno-point-and-click')

        if self.CBverbose.isChecked():
            args.insert(0, '--verbose')

        if self.CBcustomfile.isChecked():
            file_to_include = self.LEcustomfile.text()
            if file_to_include:
                args.append('-ddebug-custom-file=' + file_to_include)
        return args


