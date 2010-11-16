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
The global things in Frescobaldi.
"""

import os
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import info
import mainwindow

qApp = QApplication([os.path.abspath(sys.argv[0])] + sys.argv[1:])
QApplication.setApplicationName(info.name)
QApplication.setApplicationVersion(info.version)
QApplication.setOrganizationName(info.name)
QApplication.setOrganizationDomain(info.url)


windows = []
documents = []


def openUrl(url, encoding=None):
    """Opens the specified url or activates it if already opened.
    
    Always returns a Document instance.
    
    """
    pass

def run():
    """Enter the Qt event loop."""
    if not windows:
        mainwindow.MainWindow().show()
    sys.exit(qApp.exec_())
    
def quit():
    for window in windows:
        if not window.close():
            break

def startSession(name):
    """Switches to the given session."""
    

