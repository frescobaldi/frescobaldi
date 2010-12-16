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
Widget for search and replace.
"""

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Search(QWidget):
    def __init__(self, mainwindow):
        super(Search, self).__init__(mainwindow)
        self._currentView = None
        mainwindow.currentViewChanged.connect(self.hideWidget)
        
        hide = QAction(self)
        self.addAction(hide)
        hide.setShortcut(QKeySequence(Qt.Key_Escape))
        hide.triggered.connect(self.hideWidget)
        
    def isVisible(self):
        return bool(self.currentView())
    
    def currentView(self):
        return self._currentView and self._currentView()
    
    def setCurrentView(self, view):
        self._currentView = weakref.ref(view) if view else None
        
    def showWidget(self):
        if self.isVisible():
            self.hideWidget()
        view = self.window().currentView()
        view.showWidget(self)
        self.setCurrentView(view)
        
    def hideWidget(self):
        view = self.currentView()
        if view:
            view.hideWidget(self)
            self.setCurrentView(None)

    def find(self):
        self.setFixedHeight(30)
        self.showWidget()
        
    def replace(self):
        self.setFixedHeight(50)
        self.showWidget()
        
        
        