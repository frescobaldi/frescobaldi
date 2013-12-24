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
The SVG preview panel widget.
"""

from __future__ import unicode_literals

import os
import sys

from PyQt4 import QtCore
from PyQt4.QtGui import *

import app
import resultfiles

from . import view


class SvgView(QWidget):
    def __init__(self, dockwidget):
        super(SvgView, self).__init__(dockwidget)
        
        self._currentFiles = None
        
        self.view = view.View(self)
        
        self.pageLabel = QLabel()
        self.pageCombo = QComboBox(sizeAdjustPolicy=QComboBox.AdjustToContents)
		
        layout = QVBoxLayout(spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        hbox = QHBoxLayout(spacing=0)
        hbox.addWidget(self.pageLabel)
        hbox.addWidget(self.pageCombo)
        
        self.zoomInButton = QToolButton(autoRaise=True)
        self.zoomOutButton = QToolButton(autoRaise=True)
        self.zoomOriginalButton = QToolButton(autoRaise=True)
        ac = dockwidget.actionCollection
        self.zoomInButton.setDefaultAction(ac.svg_zoom_in)
        self.zoomOutButton.setDefaultAction(ac.svg_zoom_out)
        self.zoomOriginalButton.setDefaultAction(ac.svg_zoom_original)
        hbox.addWidget(self.zoomInButton)
        hbox.addWidget(self.zoomOutButton)
        hbox.addWidget(self.zoomOriginalButton)
        
        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addWidget(self.view)
        
        app.jobFinished.connect(self.initSvg)
        self.pageCombo.currentIndexChanged.connect(self.changePage)
        dockwidget.mainwindow().currentDocumentChanged.connect(self.initSvg)
        doc = dockwidget.mainwindow().currentDocument()
        if doc:
            self.initSvg(doc)
        app.translateUI(self)
    
    def translateUI(self):
        self.pageLabel.setText(_("Page:"))

        
    def mainwindow(self):
        return self.parent().mainwindow()       
        
    def initSvg(self, doc):
        """Opens first page of score after compilation"""
        svg_pages = resultfiles.results(doc).files('.svg')
        if svg_pages:
            svg = QtCore.QUrl(svg_pages[0])
            self.view.load(svg)       
            self._currentFiles = svg_pages
            self.setPageCombo()
			
    def setPageCombo(self):
        """Fill combobox with page numbers"""
        self.pageCombo.clear()
        self.pageCombo.addItems(map(os.path.basename, self._currentFiles))
        
    def changePage(self, page_index):
        """change page of score"""
        svg = QtCore.QUrl(self._currentFiles[page_index])
        self.view.load(svg)
		
    def clear(self):
        """Empties the view."""
        self._currentFiles = None
        nosvg = QtCore.QUrl("")
        self.view.load(nosvg)

