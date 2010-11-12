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
Frescobaldi Main Window.
"""
import itertools

from PyQt4.QtGui import QAction, QMainWindow

import app
import icons

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        
        # find an unused objectName
        names = set(win.objectName() for win in app.windows)
        for num in itertools.count(1):
            name = "MainWindow{0}".format(num)
            if name not in names:
                self.setObjectName(name)
                break
        self.setWindowIcon(icons.get('frescobaldi'))
        app.windows.append(self)
        self.createActions()
        self.createMenus()
        
        self.translateUI()
        
    def closeEvent(self, ev):
        if self.queryClose():
            ev.accept()
            app.windows.remove(self)
        else:
            ev.ignore()

    def queryClose(self):
        return True
    
    def translateUI(self):
        self.translateActions()
        self.translateMenus()
        
    def createActions(self):
        self.fileNew = QAction(icons.get('file-new'), '', self)
        self.fileOpen = QAction(icons.get('file-open'), '', self)
        
    def translateActions(self):
        self.fileNew.setText(_("&New"))
        self.fileOpen.setText(_("&Open"))
        
    def createMenus(self):
        self.fileMenu = m = self.menuBar().addMenu('')
        m.addAction(self.fileNew)
        m.addAction(self.fileOpen)
        m.addSeparator()
        
    def translateMenus(self):
        self.fileMenu.setTitle(_('&File'))
        
