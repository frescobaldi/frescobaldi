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
The score settings widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app

from . import scoreproperties

class SettingsWidget(QWidget):
   def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.scoreProperties = ScoreProperties()
        
        grid.addWidget(self.scoreProperties, 0, 0)



class ScoreProperties(QGroupBox, scoreproperties.ScoreProperties):
    def __init__(self, parent = None):
        super(ScoreProperties, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.createWidgets()
        self.layoutWidgets(layout)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.translateWidgets()
        self.setTitle(_("Score properties"))
    

