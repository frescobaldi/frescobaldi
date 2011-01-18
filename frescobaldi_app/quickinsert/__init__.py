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
The Quick Insert panel widget.
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons
import symbols


class QuickInsert(QWidget):
    def __init__(self, panel):
        super(QuickInsert, self).__init__(panel)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.directionLabel = QLabel()
        self.direction = QComboBox()
        self.direction.addItems(['', '', ''])
        self.direction.setItemIcon(0, icons.get("arrow-up"))
        self.direction.setItemIcon(2, icons.get("arrow-down"))
        self.direction.setCurrentIndex(1)
        hor = QHBoxLayout()
        hor.setContentsMargins(0, 0, 0, 0)
        hor.addWidget(self.directionLabel)
        hor.addWidget(self.direction)
        layout.addLayout(hor)
        
        self.toolbox = ToolBox(self)
        layout.addWidget(self.toolbox)
        app.translateUI(self)
        
    def translateUI(self):
        self.directionLabel.setText(_("Direction:"))
        for item, text in enumerate((_("Up"), _("Neutral"), _("Down"))):
            self.direction.setItemText(item, text)
    
    def actionForName(self, name):
        """This is called by the ShortcutCollection of our dockwidget if the user presses a key."""
        print "Action",name,"requested!!"
        a = QAction(None)
        a.setText("Slur")
        a.setIcon(symbols.icon('bar_single'))
        return a


class ToolBox(QToolBox):
    pass


