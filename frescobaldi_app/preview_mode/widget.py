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

        # Load settings and set checkbox state
        s = QSettings()
        s.beginGroup('lilypond_settings')
        self.checkOption(s, 'skylines')
        self.checkOption(s, 'control-points')
        self.checkOption(s, 'voices')
        self.checkOption(s, 'directions')
        self.checkOption(s, 'grob-anchors')

        # Compose layout
        layout.addWidget(self.CBskylines)
        layout.addWidget(self.CBcontrolpoints)
        layout.addWidget(self.CBcolorvoices)
        layout.addWidget(self.CBcolordirections)
        layout.addWidget(self.CBgrobanchors)
        layout.addStretch(1)
        
        # Connect slots
        self.CBskylines.toggled.connect(self.toggleOption)
        self.CBcontrolpoints.toggled.connect(self.toggleOption)
        self.CBcolorvoices.toggled.connect(self.toggleOption)
        self.CBcolordirections.toggled.connect(self.toggleOption)
        self.CBgrobanchors.toggled.connect(self.toggleOption)
        
        self.translateUI()
    
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
        self.CBcolordirections.setText(_("Color \\xxxUp/Down"))
        self.CBcolordirections.setToolTip(_(
            "Highlight elements that are explicitly switched up- or "
            "downwards using \\xxxUp or \\xxxDown commands"))
        self.CBgrobanchors.setText(_("Display Grob Anchors"))
        self.CBgrobanchors.setToolTip(_(
            "Display a red dot at the anchor point of each grob"))
        
    def checkOption(self, s, key):
        self.options[key].setChecked(preview_mode.load_bool_option(s, key))

    def writeSetting(self, option, state):
        s = QSettings()
        s.beginGroup("lilypond_settings")
        s.setValue(option, state)

    def toggleOption(self, state):
        for key in self.options:
            if self.options[key] == self.sender():
                print key
                self.writeSetting(key, state)
