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

import sys
from PyQt4 import QtCore
from PyQt4.QtGui import *

import app
import resultfiles

from . import svgscene

class SvgView(QWidget):
    def __init__(self, dockwidget):
        super(SvgView, self).__init__(dockwidget)
        
        self._currentFiles = None
        
        self.scene = svgscene.SvgScene()
        
        self.pageLabel = QLabel()
        self.pageLabel.setText(_("Page:"))
        self.pageCombo = QComboBox()
		
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.pageLabel)
        layout.addWidget(self.pageCombo)
        layout.addWidget(self.scene.view)
        self.scene.view.show()
        
        app.jobFinished.connect(self.initSvg)
        self.pageCombo.currentIndexChanged.connect(self.changePage)
        
    def mainwindow(self):
        return self.parent().mainwindow()       
        
    def initSvg(self, doc):
        """Opens first page of score after compilation"""
        self.scene.setDoc(doc, self.mainwindow())
        svg_pages = resultfiles.results(doc).files('.svg')
        if svg_pages:
            svg = QtCore.QUrl(svg_pages[0])
            self.scene.webview.load(svg)       
            self._currentFiles = svg_pages
            self.setPageCombo()
			
    def setPageCombo(self):
        """Fill combobox with page numbers"""
        self.pageCombo.clear()
        for p in range (1, len(self._currentFiles)+1):
            self.pageCombo.addItem(str(p))			
        
    def changePage(self, page_index):
        """change page of score"""
        svg = QtCore.QUrl(self._currentFiles[page_index])
        self.scene.webview.load(svg)
		
    def clear(self):
        """Empties the view."""
        self._currentFiles = None
        nosvg = QtCore.QUrl("")
        self.scene.webview.load(nosvg)

