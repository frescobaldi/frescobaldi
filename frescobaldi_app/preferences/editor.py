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
Helper application preferences.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import (
    QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QScrollArea, QSpinBox, 
    QVBoxLayout, QWidget)

import app
import util
import qutil
import icons
import preferences
import widgets.urlrequester


class Editor(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Editor, self).__init__(dialog)
        
        layout = QVBoxLayout(margin=0, spacing=0)
        self.setLayout(layout)
        scrollarea = QScrollArea(frameWidth=0, frameShape=QScrollArea.NoFrame)
        layout.addWidget(scrollarea)
        widget = QWidget(scrollarea)
        layout = QVBoxLayout()
        widget.setLayout(layout)
        scrollarea.setWidget(widget)
        scrollarea.setWidgetResizable(True)
        
        layout.addWidget(Highlighting(self))
        layout.addStretch()


class Highlighting(preferences.Group):
    def __init__(self, page):
        super(Highlighting, self).__init__(page)
        
        layout = QGridLayout(spacing=1)
        self.setLayout(layout)
        
        self.messageLabel = QLabel(wordWrap=True)
        layout.addWidget(self.messageLabel, 0, 0, 1, 2)
        self.labels = {}
        self.entries = {}
        for row, (name, title, default) in enumerate(self.items(), 1):
            self.labels[name] = l = QLabel()
            self.entries[name] = e = QSpinBox()
            e.setRange(0, 60)
            e.valueChanged.connect(page.changed)
            layout.addWidget(l, row, 0)
            layout.addWidget(e, row, 1)
            
        app.translateUI(self)
    
    def items(self):
        """
        Yields (name, title, default) tuples for every setting in this group.
        Default is understood in seconds.
        """
        yield "match", _("Matching Item:"), 1
        
    def translateUI(self):
        self.setTitle(_("Highlighting Options"))
        self.messageLabel.setText(_(
            "Below you can define how long "
            "\"matching\" items like matching brackets or the items "
            "linked through Point-and-Click are highlighted."))
        for name, title, default in self.items():
            self.entries[name].setSpecialValueText(_("Infinite"))
            self.entries[name].setSuffix(_("abbreviation for \"seconds\"", " sec"))
            self.labels[name].setText(title)
    
    def loadSettings(self):
        s = QSettings()
        s.beginGroup("editor_highlighting")
        for name, title, default in self.items():
            self.entries[name].setValue(s.value(name, default, int))
    
    def saveSettings(self):
        s= QSettings()
        s.beginGroup("editor_highlighting")
        for name, title, default in self.items():
            s.setValue(name, self.entries[name].value())
