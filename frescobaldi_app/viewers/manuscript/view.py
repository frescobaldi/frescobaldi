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
The Manuscript view 
"""

from __future__ import unicode_literals

from PyQt4 import QtCore
from PyQt4 import QtGui

import app

class View(QtGui.QScrollArea):
    """Display a series of manuscript pages"""
    def __init__(self, parent):
        super(View, self).__init__(parent)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

        # initialize with empty widget
        self.setWidget(QtGui.QWidget())

    def open(self, image_list, pdf = False):
        """Open a list of images.
        Open an image viewer or a PDF viewer."""
        import manuscriptcontainer
        self.setWidget(manuscriptcontainer.open(self, image_list, pdf))

    def mainwindow(self):
        return self.parent().mainwindow()

    def readSettings(self):
        """Reads the settings from the user's preferences."""
        pass
