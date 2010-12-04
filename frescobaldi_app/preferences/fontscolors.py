# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Fonts and Colors preferences page.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
    preferences,
)

from ..widgets.schemeselector import SchemeSelector


class FontsColors(preferences.Page):
    def __init__(self, dialog):
        super(FontsColors, self).__init__(dialog)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.scheme = SchemeSelector(self)
        layout.addWidget(self.scheme)
        
        hbox = QHBoxLayout()
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAnimated(True)
        self.stack = QStackedWidget(self)
        hbox.addWidget(self.tree)
        hbox.addWidget(self.stack)
        layout.addLayout(hbox)
        
        self.fontButton = QPushButton(_("Change Font..."))
        layout.addWidget(self.fontButton)
        
    def loadSettings(self):
        self.scheme.loadSettings("editor_scheme", "editor_schemes")
        
    def saveSettings(self):
        self.scheme.saveSettings("editor_scheme", "editor_schemes", "fontscolor")
        
