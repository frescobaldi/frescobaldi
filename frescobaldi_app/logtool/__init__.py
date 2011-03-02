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
The log dockwindow.
"""




from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import panels


class LogTool(panels.Panel):
    """A dockwidget showing the log of running Jobs."""
    def __init__(self, mainwindow):
        super(LogTool, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+L"))
        mainwindow.addDockWidget(Qt.BottomDockWidgetArea, self)
    
    def translateUI(self):
        self.setWindowTitle(_("LilyPond Log"))
        self.toggleViewAction().setText(_("LilyPond &Log"))
        
    def createWidget(self):
        from . import logwidget
        return logwidget.LogWidget(self)
        
