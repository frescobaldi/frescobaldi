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
The Preferences Dialog.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import app


class PreferencesDialog(QDialog):
    
    def __init__(self, parent=None):
        super(PreferencesDialog, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        
        # listview to the left, stacked widget to the right
        top = QHBoxLayout()
        layout.addLayout(top)
        
        self.pagelist = QListView(self)
        self.stack = QStackedWidget(self)
        top.addWidget(self.pagelist)
        top.addWidget(self.stack)
        
        b = self.buttons = QDialogButtonBox(self)
        b.setStandardButtons(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
            | QDialogButtonBox.Apply
            | QDialogButtonBox.Reset
            | QDialogButtonBox.Help)
            
        layout.addWidget(self.buttons)
        
        