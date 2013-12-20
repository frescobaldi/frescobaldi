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
The SVG preview panel.

For now this previews a SVG-file.
The plan is that it later in devolpment also will be
possible to edit both the SVG-file and the LilyPond source by this panel. 

"""

from __future__ import unicode_literals

from PyQt4.QtCore import Qt
from PyQt4.QtGui import (QAction, QKeySequence)

import app
import actioncollection
import actioncollectionmanager
import panel

class SvgViewPanel(panel.Panel):
    def __init__(self, mainwindow):
        super(SvgViewPanel, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+S"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        
        ac = self.actionCollection = Actions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)		
		
    def translateUI(self):
        self.setWindowTitle(_("window title", "SVG View"))
        self.toggleViewAction().setText(_("&SVG View"))
        
    def createWidget(self):
        import widget
        w = widget.SvgView(self)
        return w

class Actions(actioncollection.ActionCollection):
    name = "svgview"
    def createActions(self, panel):
        pass
