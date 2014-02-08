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
The global menubar on Mac OS X.

This menubar is only created when there is no MainWindow. As soon a MainWindow
is created, this global menubar is deleted, and Mac OS X will use the menubar
from the MainWindow.

"""

from __future__ import unicode_literals

import sys
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import util
import qutil
import icons
import info

from . import use_osx_menu_roles


def setup():
    """Create the global menu bar."""
    global _menubar
    _menubar = menubar()

@app.mainwindowCreated.connect
def delete():
    """Delete the global menu bar."""
    global _menubar
    _menubar = None

def menubar():
    """Return a newly created parent-less menu bar that's used when there is no main window."""
    m = QMenuBar()
    m.addMenu(menu_file(m))
    m.addMenu(menu_edit(m))
    m.addMenu(menu_help(m))

    return m

def menu_file(parent):
    m = QMenu(parent)
    m.setTitle(_("menu title", "&File"))
    m.addAction(icons.get('document-new'), _("action: new document", "&New"), file_new)
    m.addAction(icons.get('document-open'), _("&Open..."), file_open)
    m.addSeparator()
    m.addMenu(menu_file_open_recent(m))
    m.addSeparator()
    role = QAction.QuitRole if use_osx_menu_roles() else QAction.NoRole
    m.addAction(icons.get('application-exit'), _("&Quit"), app.qApp.quit).setMenuRole(role)
    return m

def menu_file_open_recent(parent):
    m = QMenu(parent)
    m.setTitle(_("Open &Recent"))
    m.triggered.connect(slot_file_open_recent_action, Qt.QueuedConnection)
    import recentfiles
    for url in recentfiles.urls():
        f = url.toLocalFile()
        dirname, basename = os.path.split(f)
        text = "{0}  ({1})".format(basename, util.homify(dirname))
        m.addAction(text).url = url
    qutil.addAccelerators(m.actions())
    return m
    
def menu_edit(parent):
    m = QMenu(parent)
    m.setTitle(_("menu title", "&Edit"))
    role = QAction.PreferencesRole if use_osx_menu_roles() else QAction.NoRole
    m.addAction(icons.get('preferences-system'), _("Pr&eferences..."), edit_preferences).setMenuRole(role)
    return m

def menu_help(parent):
    m = QMenu(parent)
    m.setTitle(_('menu title', '&Help'))
    role = QAction.AboutRole if use_osx_menu_roles() else QAction.NoRole
    m.addAction(icons.get('help-about'), _("&About {appname}...").format(appname=info.appname), help_about).setMenuRole(role)
    return m

def mainwindow():
    """Create, show() and return a new MainWindow."""
    import mainwindow
    w = mainwindow.MainWindow()
    w.show()
    return w

def file_new():
    mainwindow().newDocument()

def file_open():
    filetypes = app.filetypes('.ly')
    caption = app.caption(_("dialog title", "Open File"))
    directory = app.basedir()
    files = QFileDialog.getOpenFileNames(None, caption, directory, filetypes)
    if files:
        win = mainwindow()
        docs = [win.openUrl(QUrl.fromLocalFile(f)) for f in files]
        if docs:
            win.setCurrentDocument(docs[-1])

def slot_file_open_recent_action(action):
    url = action.url
    w = mainwindow()
    w.setCurrentDocument(w.openUrl(url))

def edit_preferences():
    import preferences
    # TODO: make it possible to run Preferences without a Main Window.
    # Currently the Keyboard Shortcuts section needs the mainwindow to get
    # the current shortcuts.
    preferences.PreferencesDialog(mainwindow()).exec_()

def help_about():
    import about
    about.AboutDialog(None).exec_()


