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
# import itertools

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import preview_mode


class Widget(QWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.options = {}
        # Skylines checkbox
        self.CBskylines = QCheckBox()
        self.options['skylines'] = self.CBskylines
        # Control-points checkbox
        self.CBcontrolpoints = QCheckBox()
        self.options['control-points'] = self.CBcontrolpoints
        # Color-voices checkbox
        self.CBcolorvoices = QCheckBox()
        self.options['voices'] = self.CBcolorvoices
        # Color-directions checkbox
        self.CBcolordirections = QCheckBox()
        self.options['directions'] = self.CBcolordirections
        # grob-anchors checkbox
        self.CBgrobanchors = QCheckBox()
        self.options['grob-anchors'] = self.CBgrobanchors
        # grob-names checkbox
        self.CBgrobnames = QCheckBox()
        self.options['grob-names'] = self.CBgrobnames
        # paper-columns checkbox
        self.CBpapercolumns = QCheckBox()
        self.options['paper-columns'] = self.CBpapercolumns
        # annotate-spacing checkbox
        self.CBannotatespacing = QCheckBox()
        self.options['annotate-spacing'] = self.CBannotatespacing
        # custom-file checkbox and input field
        self.GBcustomfile = QGroupBox()
        self.GBcustomfile.setCheckable(True)
        self.options['custom-file'] = self.GBcustomfile
        self.LEcustomfile = QLineEdit()
        
        # Compose layout
        self.customfile_layout = QVBoxLayout()
        self.customfile_layout.addWidget(self.LEcustomfile)
        self.GBcustomfile.setLayout(self.customfile_layout)
        layout.addWidget(self.CBcontrolpoints)
        layout.addWidget(self.CBcolorvoices)
        layout.addWidget(self.CBcolordirections)
        layout.addWidget(self.CBgrobanchors)
        layout.addWidget(self.CBgrobnames)
        layout.addWidget(self.CBskylines)
        layout.addWidget(self.CBpapercolumns)
        layout.addWidget(self.CBannotatespacing)
        layout.addWidget(self.GBcustomfile)
        layout.addStretch(1)
        
        # Connect slots
        self.CBskylines.toggled.connect(self.toggleOption)
        self.CBcontrolpoints.toggled.connect(self.toggleOption)
        self.CBcolorvoices.toggled.connect(self.toggleOption)
        self.CBcolordirections.toggled.connect(self.toggleOption)
        self.CBgrobanchors.toggled.connect(self.toggleOption)
        self.CBgrobnames.toggled.connect(self.toggleOption)
        self.GBcustomfile.toggled.connect(self.toggleOption)
        self.CBpapercolumns.toggled.connect(self.toggleOption)
        self.CBannotatespacing.toggled.connect(self.toggleOption)
        self.LEcustomfile.textEdited.connect(self.customFileEdited)
        
        app.translateUI(self)
        self.loadSettings()
    
    def translateUI(self):
        self.CBskylines.setText(_("Display Skylines"))
        self.CBskylines.setToolTip(_(
            "Display the skylines that LilyPond "
            "uses to detect collisions."))
        self.CBcontrolpoints.setText(_("Display Control Points"))
        self.CBcontrolpoints.setToolTip(_(
            "Display the control points that "
            "determine curve shapes"))
        self.CBcolorvoices.setText(_("Color \\voiceXXX"))
        self.CBcolorvoices.setToolTip(_(
            "Highlight notes that are explicitly "
            "set to \\voiceXXX"))
        self.CBcolordirections.setText(_("Color explicit directions"))
        self.CBcolordirections.setToolTip(_(
            "Highlight elements that are explicitly switched up- or downwards"))
        self.CBgrobanchors.setText(_("Display Grob Anchors"))
        self.CBgrobanchors.setToolTip(_(
            "Display a dot at the anchor point of each grob"))
        self.CBgrobnames.setText(_("Display Grob Names"))
        self.CBgrobnames.setToolTip(_(
            "Display the name of each grob"))
        self.CBpapercolumns.setText(_("Debug Paper Columns"))
        self.CBpapercolumns.setToolTip(_(
            "Display info on the paper columns"))
        self.CBannotatespacing.setText(_("Annotate Spacing"))
        self.CBannotatespacing.setToolTip(_(
            "Use LilyPond's \"annotate spacing\" option to\n"
            "display measurement information"))
        self.GBcustomfile.setTitle(_("Include Custom File:"))
        self.GBcustomfile.setToolTip(_(
            "Include a custom file with definitions\n"
            "for additional Debug Modes"))
        self.LEcustomfile.setToolTip(_(
            "Filename to be included"))
        
    def loadSettings(self):
        """Called on construction. Load settings and set checkboxes state."""
        s = QSettings()
        s.beginGroup('lilypond_settings')
        def checkOption(key):
            self.options[key].setChecked(s.value(key, False, bool))
        checkOption('skylines')
        checkOption('control-points')
        checkOption('voices')
        checkOption('directions')
        checkOption('grob-anchors')
        checkOption('grob-names')
        checkOption('custom-file')
        checkOption('paper-columns')
        checkOption('annotate-spacing')
        self.LEcustomfile.setText(s.value('custom-filename', '', type("")))
        
    def customFileEdited(self):
        """Called when the user types in the custom file entry."""
        s = QSettings()
        s.beginGroup("lilypond_settings")
        s.setValue("custom-filename", self.LEcustomfile.text())

    def toggleOption(self, state):
        """Called when a checkbox is toggled by the user."""
        for key in self.options:
            if self.options[key] == self.sender():
                s = QSettings()
                s.beginGroup("lilypond_settings")
                s.setValue(key, state)
                break


