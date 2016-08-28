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
The SVG preview panel.

This previews a SVG-file with initial editing abilities. 

"""


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QLabel

import app
import actioncollection
import actioncollectionmanager
import panel
import icons


class SvgViewPanel(panel.Panel):
    def __init__(self, mainwindow):
        super(SvgViewPanel, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+G"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        
        ac = self.actionCollection = Actions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.svg_zoom_in.triggered.connect(self.zoomIn)
        ac.svg_zoom_out.triggered.connect(self.zoomOut)
        ac.svg_zoom_original.triggered.connect(self.zoomOriginal)
        
    def translateUI(self):
        self.setWindowTitle(_("window title", "SVG View"))
        self.toggleViewAction().setText(_("SV&G View"))
        
    def createWidget(self):
        try:
            from . import widget
        except ImportError as err:
            return QLabel(str(err),self) # Display error as widget
        w = widget.SvgView(self)
        return w
    
    def zoomIn(self):
        self.activate()
        self.widget().view.zoomIn()
        
    def zoomOut(self):
        self.activate()
        self.widget().view.zoomOut()
        
    def zoomOriginal(self):
        self.activate()
        self.widget().view.zoomOriginal()


class Actions(actioncollection.ActionCollection):
    name = "svgview"
    def createActions(self, panel):
        self.svg_zoom_in = QAction(panel)
        self.svg_zoom_out = QAction(panel)
        self.svg_zoom_original = QAction(panel)
        
        self.svg_zoom_in.setIcon(icons.get('zoom-in'))
        self.svg_zoom_out.setIcon(icons.get('zoom-out'))
        self.svg_zoom_original.setIcon(icons.get('zoom-original'))
        
    def translateUI(self):
        self.svg_zoom_in.setText(_("Zoom &In"))
        self.svg_zoom_out.setText(_("Zoom &Out"))
        self.svg_zoom_original.setText(_("Original &Size"))


