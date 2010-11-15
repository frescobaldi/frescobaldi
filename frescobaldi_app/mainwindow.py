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

from PyQt4.QtCore import *
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
        if len(app.windows) > 1 or self.queryClose():
            ev.accept()
            app.windows.remove(self)
        else:
            ev.ignore()

    def queryClose(self):
        return True

    def createActions(self):
        self.actionCollection = ac = ActionCollection(self)
        
        # recent files
        self.menu_recent_files = m = QMenu()
        ac.file_open_recent.setMenu(m)
        
        # connections
        ac.file_quit.triggered.connect(self.close)
        
    def createMenus(self):
        ac = self.actionCollection
        self.menu_file = m = self.menuBar().addMenu('')
        m.addAction(ac.file_new)
        m.addSeparator()
        m.addAction(ac.file_open)
        m.addAction(ac.file_open_recent)
        m.addAction(ac.file_open_current_directory)
        m.addSeparator()
        m.addAction(ac.file_save)
        m.addAction(ac.file_save_as)
        m.addSeparator()
        m.addAction(ac.file_save_all)
        m.addSeparator()
        m.addAction(ac.file_print_music)
        m.addAction(ac.file_print_source)
        m.addSeparator()
        m.addAction(ac.file_close)
        m.addAction(ac.file_close_other)
        m.addSeparator()
        m.addAction(ac.file_quit)
        
        self.menu_edit = m = self.menuBar().addMenu('')
        m.addAction(ac.edit_undo)
        m.addAction(ac.edit_redo)
        m.addSeparator()
        m.addAction(ac.edit_cut_assign)
        m.addAction(ac.edit_cut)
        m.addAction(ac.edit_copy)
        m.addAction(ac.edit_paste)
        m.addSeparator()
        m.addAction(ac.edit_select_all)
        m.addAction(ac.edit_select_current_toplevel)
        m.addAction(ac.edit_select_none)
        m.addSeparator()
        m.addAction(ac.edit_find)
        m.addAction(ac.edit_find_next)
        m.addAction(ac.edit_find_previous)
        m.addAction(ac.edit_replace)
        m.addSeparator()
        m.addAction(ac.edit_preferences)
        
        self.menu_view = m = self.menuBar().addMenu('')
        self.menu_lilypond = m = self.menuBar().addMenu('')
        self.menu_tools = m = self.menuBar().addMenu('')
        self.menu_window = m = self.menuBar().addMenu('')
        self.menu_sessions = m = self.menuBar().addMenu('')
        self.menu_help = m = self.menuBar().addMenu('')
        
    def translateUI(self):
        self.actionCollection.translate()
        self.menu_file.setTitle(_('&File'))
        self.menu_edit.setTitle(_('&Edit'))
        self.menu_view.setTitle(_('&View'))
        self.menu_lilypond.setTitle(_('&LilyPond'))
        self.menu_tools.setTitle(_('&Tools'))
        self.menu_window.setTitle(_('&Window'))
        self.menu_sessions.setTitle(_('&Sessions'))
        self.menu_help.setTitle(_('&Help'))
        

class ActionCollection:
    def __init__(self, mainwindow):
        self.file_new = QAction(mainwindow)
        self.file_open = QAction(mainwindow)
        self.file_open_recent = QAction(mainwindow)
        self.file_open_current_directory = QAction(mainwindow)
        self.file_save = QAction(mainwindow)
        self.file_save_as = QAction(mainwindow)
        self.file_save_all = QAction(mainwindow)
        self.file_print_source = QAction(mainwindow)
        self.file_print_music = QAction(mainwindow)
        self.file_close = QAction(mainwindow)
        self.file_close_other = QAction(mainwindow)
        self.file_quit = QAction(mainwindow)
        
        self.edit_undo = QAction(mainwindow)
        self.edit_redo = QAction(mainwindow)
        self.edit_cut_assign = QAction(mainwindow)
        self.edit_cut = QAction(mainwindow)
        self.edit_copy = QAction(mainwindow)
        self.edit_paste = QAction(mainwindow)
        self.edit_select_all = QAction(mainwindow)
        self.edit_select_current_toplevel = QAction(mainwindow)
        self.edit_select_none = QAction(mainwindow)
        self.edit_find = QAction(mainwindow)
        self.edit_find_next = QAction(mainwindow)
        self.edit_find_previous = QAction(mainwindow)
        self.edit_replace = QAction(mainwindow)
        self.edit_preferences = QAction(mainwindow)
        
        
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
        
        self.edit_undo.setIcon(icons.get('edit-undo'))
        self.edit_redo.setIcon(icons.get('edit-redo'))
        self.edit_cut_assign.setIcon(icons.get('edit-cut'))
        self.edit_cut.setIcon(icons.get('edit-cut'))
        self.edit_copy.setIcon(icons.get('edit-copy'))
        self.edit_paste.setIcon(icons.get('edit-paste'))
        self.edit_select_all.setIcon(icons.get('edit-select-all'))
        self.edit_select_current_toplevel.setIcon(icons.get('edit-select'))
        self.edit_find.setIcon(icons.get('edit-find'))
        self.edit_find_next.setIcon(icons.get('go-down-search'))
        self.edit_find_previous.setIcon(icons.get('go-up-search'))
        self.edit_replace.setIcon(icons.get('edit-find-replace'))
        self.edit_preferences.setIcon(icons.get('configure'))
        
        # shortcuts
        self.file_new.setShortcuts(QKeySequence.New)
        self.file_open.setShortcuts(QKeySequence.Open)
        self.file_save.setShortcuts(QKeySequence.Save)
        self.file_save_as.setShortcuts(QKeySequence.SaveAs)
        self.file_print_music.setShortcuts(QKeySequence.Print)
        self.file_close.setShortcuts(QKeySequence.Close)
        self.file_quit.setShortcuts(QKeySequence.Quit)
        
        self.edit_undo.setShortcuts(QKeySequence.Undo)
        self.edit_redo.setShortcuts(QKeySequence.Redo)
        self.edit_cut_assign.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_C))
        self.edit_cut.setShortcuts(QKeySequence.Cut)
        self.edit_copy.setShortcuts(QKeySequence.Copy)
        self.edit_paste.setShortcuts(QKeySequence.Paste)
        self.edit_select_all.setShortcuts(QKeySequence.SelectAll)
        self.edit_select_current_toplevel.setShortcut(QKeySequence(Qt.SHIFT+Qt.CTRL+Qt.Key_B))
        self.edit_select_none.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_A))
        self.edit_find.setShortcuts(QKeySequence.Find)
        self.edit_find_next.setShortcuts(QKeySequence.FindNext)
        self.edit_find_previous.setShortcuts(QKeySequence.FindPrevious)
        self.edit_replace.setShortcuts(QKeySequence.Replace)

    def translate(self):
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

        self.edit_undo.setText(_("&Undo"))
        self.edit_redo.setText(_("Re&do"))
        self.edit_cut_assign.setText(_("Cut and Assign..."))
        self.edit_cut.setText(_("Cu&t"))
        self.edit_copy.setText(_("&Copy"))
        self.edit_paste.setText(_("&Paste"))
        self.edit_select_all.setText(_("Select &All"))
        self.edit_select_current_toplevel.setText(_("Select &Block"))
        self.edit_select_none.setText(_("Select &None"))
        self.edit_find.setText(_("&Find..."))
        self.edit_find_next.setText(_("Find Ne&xt"))
        self.edit_find_previous.setText(_("Find Pre&vious"))
        self.edit_replace.setText(_("&Replace..."))
        self.edit_preferences.setText(_("&Preferences..."))
        
        