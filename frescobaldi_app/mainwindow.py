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

from PyQt4.QtGui import *

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
        self.file_new = QAction(self)
        self.file_open = QAction(self)
        self.file_open_recent = QAction(self)
        self.file_open_current_directory = QAction(self)
        self.file_save = QAction(self)
        self.file_save_as = QAction(self)
        self.file_save_all = QAction(self)
        self.file_print_source = QAction(self)
        self.file_print_music = QAction(self)
        self.file_close = QAction(self)
        self.file_close_other = QAction(self)
        self.file_quit = QAction(self)
        
        # recent files
        self.menu_recent_files = m = QMenu()
        self.file_open_recent.setMenu(m)
        
        # icons
        self.file_new.setIcon(icons.get('document-new'))
        self.file_open.setIcon(icons.get('document-open'))
        self.file_open_recent.setIcon(icons.get('document-open-recent'))
        self.file_open_current_directory.setIcon(icons.get('document-open-folder'))
        self.file_save.setIcon(icons.get('document-save'))
        self.file_save_as.setIcon(icons.get('document-save-as'))
        self.file_save_all.setIcon(icons.get('document-save-all'))
        self.file_print_source.setIcon(icons.get('document-print'))
        self.file_print_music.setIcon(icons.get('document-print'))
        self.file_close.setIcon(icons.get('document-close'))
        self.file_quit.setIcon(icons.get('application-exit'))
        
        # shortcuts
        self.file_new.setShortcuts(QKeySequence.New)
        self.file_open.setShortcuts(QKeySequence.Open)
        self.file_save.setShortcuts(QKeySequence.Save)
        self.file_save_as.setShortcuts(QKeySequence.SaveAs)
        self.file_print_music.setShortcuts(QKeySequence.Print)
        self.file_close.setShortcuts(QKeySequence.Close)
        self.file_quit.setShortcuts(QKeySequence.Quit)
        
        # connections
        self.file_quit.triggered.connect(self.close)
        
    def translateActions(self):
        self.file_new.setText(_("&New"))
        self.file_open.setText(_("&Open..."))
        self.file_open_recent.setText(_("Open &Recent"))
        self.file_open_current_directory.setText(_("Open Current Directory"))
        self.file_save.setText(_("&Save"))
        self.file_save_as.setText(_("Save &As..."))
        self.file_save_all.setText(_("Save All"))
        self.file_print_music.setText(_("&Print &Music..."))
        self.file_print_source.setText(_("Print Source..."))
        self.file_close.setText(_("&Close"))
        self.file_close_other.setText(_("Close Other Documents"))
        self.file_quit.setText(_("&Quit"))
        
    def createMenus(self):
        self.menu_file = m = self.menuBar().addMenu('')
        m.addAction(self.file_new)
        m.addSeparator()
        m.addAction(self.file_open)
        m.addAction(self.file_open_recent)
        m.addAction(self.file_open_current_directory)
        m.addSeparator()
        m.addAction(self.file_save)
        m.addAction(self.file_save_as)
        m.addSeparator()
        m.addAction(self.file_save_all)
        m.addSeparator()
        m.addAction(self.file_print_music)
        m.addAction(self.file_print_source)
        m.addSeparator()
        m.addAction(self.file_close)
        m.addAction(self.file_close_other)
        m.addSeparator()
        m.addAction(self.file_quit)
        
    def translateMenus(self):
        self.menu_file.setTitle(_('&File'))
        


