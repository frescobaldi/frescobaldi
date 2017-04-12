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


import sys
import os

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QAction, QFileDialog, QMenu, QMenuBar

import app
import util
import qutil
import icons
import appinfo

from . import use_osx_menu_roles


def setup():
    """Create the global menu bar, and switch to no-session."""
    global _menubar
    _menubar = menubar()
    import sessions
    sessions.setCurrentSession(None)

@app.mainwindowCreated.connect
def delete():
    """Delete the global menu bar."""
    global _menubar
    _menubar.deleteLater()
    _menubar = None

def menubar():
    """Return a newly created parent-less menu bar that's used when there is no main window."""
    m = QMenuBar()
    m.addMenu(menu_file(m))
    m.addMenu(menu_edit(m))
    m.addMenu(menu_window(m))
    m.addMenu(menu_sessions(m))
    m.addMenu(menu_help(m))
    return m

def menu_file(parent):
    m = QMenu(parent)
    m.setTitle(_("menu title", "&File"))
    m.addAction(icons.get('document-new'), _("action: new document", "&New"), file_new)
    m.addMenu(menu_file_new_from_template(m))
    m.addAction(icons.get('tools-score-wizard'), _("New Score with &Wizard..."), file_new_with_wizard)
    m.addSeparator()
    m.addAction(icons.get('document-open'), _("&Open..."), file_open)
    m.addMenu(menu_file_open_recent(m))
    m.addSeparator()
    m.addMenu(menu_file_import(m))
    m.addSeparator()
    role = QAction.QuitRole if use_osx_menu_roles() else QAction.NoRole
    m.addAction(icons.get('application-exit'), _("&Quit"), app.qApp.quit).setMenuRole(role)
    return m

def menu_file_new_from_template(parent):
    m = QMenu(parent)
    m.setTitle(_("New from &Template"))
    m.triggered.connect(slot_file_new_from_template_action)
    from snippet import model, actions, snippets
    groups = {}
    for name in sorted(model.model().names()):
        variables = snippets.get(name).variables
        group = variables.get('template')
        if group:
            action = actions.action(name, m)
            if action:
                groups.setdefault(group, []).append(action)
    for group in sorted(groups):
        for action in groups[group]:
            m.addAction(action)
        m.addSeparator()
    qutil.addAccelerators(m.actions())
    return m

def menu_file_open_recent(parent):
    m = QMenu(parent)
    m.setTitle(_("Open &Recent"))
    m.triggered.connect(slot_file_open_recent_action)
    import recentfiles
    for url in recentfiles.urls():
        f = url.toLocalFile()
        dirname, basename = os.path.split(f)
        text = "{0}  ({1})".format(basename, util.homify(dirname))
        m.addAction(text).url = url
    qutil.addAccelerators(m.actions())
    return m

def menu_file_import(parent):
    m = QMenu(parent)
    m.setTitle(_("submenu title", "&Import"))
    m.addAction(_("Import MusicXML..."), file_import_musicxml)
    return m

def menu_edit(parent):
    m = QMenu(parent)
    m.setTitle(_("menu title", "&Edit"))
    role = QAction.PreferencesRole if use_osx_menu_roles() else QAction.NoRole
    m.addAction(icons.get('preferences-system'), _("Pr&eferences..."), edit_preferences).setMenuRole(role)
    return m

def menu_window(parent):
    m = QMenu(parent)
    m.setTitle(_('menu title', '&Window'))
    m.addAction(icons.get('window-new'), _("New &Window"), file_new)
    return m

def menu_sessions(parent):
    m = QMenu(parent)
    m.setTitle(_('menu title', '&Session'))
    m.triggered.connect(slot_session_action)
    import sessions
    for name in sessions.sessionNames():
        a = m.addAction(name.replace('&', '&&'))
        a.setObjectName(name)
    qutil.addAccelerators(m.actions())
    return m

def menu_help(parent):
    m = QMenu(parent)
    m.setTitle(_('menu title', '&Help'))
    role = QAction.AboutRole if use_osx_menu_roles() else QAction.NoRole
    m.addAction(icons.get('help-about'), _("&About {appname}...").format(appname=appinfo.appname), help_about).setMenuRole(role)
    return m

def mainwindow():
    """Create, show() and return a new MainWindow."""
    import mainwindow
    w = mainwindow.MainWindow()
    w.show()
    w.activateWindow()
    return w

def file_new():
    mainwindow().newDocument()

def file_new_with_wizard():
    w = mainwindow()
    w.newDocument()
    import scorewiz
    scorewiz.ScoreWizard.instance(w).showDialog()

def file_open():
    filetypes = app.filetypes('.ly')
    caption = app.caption(_("dialog title", "Open File"))
    directory = app.basedir()
    files = QFileDialog.getOpenFileNames(None, caption, directory, filetypes)[0]
    if files:
        w = mainwindow()
        w.openUrls([QUrl.fromLocalFile(f) for f in files])
        if not app.documents:
            w.cleanStart()

def slot_file_new_from_template_action(action):
    name = action.objectName()
    d = app.openUrl(QUrl())
    win = mainwindow()
    win.setCurrentDocument(d)
    from snippet import insert, snippets
    view = win.currentView()
    view.setFocus()
    insert.insert(name, view)
    d.setUndoRedoEnabled(False)
    d.setUndoRedoEnabled(True) # d.clearUndoRedoStacks() only in Qt >= 4.7
    d.setModified(False)
    if 'template-run' in snippets.get(name).variables:
        import engrave
        engrave.engraver(win).engrave('preview', d)

def slot_file_open_recent_action(action):
    w = mainwindow()
    d = w.openUrl(action.url)
    if d:
        w.setCurrentDocument(d)

def file_import_musicxml():
    w = mainwindow()
    w.newDocument()
    import file_import
    file_import.FileImport.instance(w).importMusicXML()

def edit_preferences():
    import preferences
    # TODO: make it possible to run Preferences without a Main Window.
    # Currently the Keyboard Shortcuts section needs the mainwindow to get
    # the current shortcuts.
    w = mainwindow()
    w.newDocument()
    preferences.PreferencesDialog(w).exec_()

def slot_session_action(action):
    name = action.objectName()
    import sessions
    doc = sessions.loadSession(name) or app.openUrl(QUrl())
    w = mainwindow()
    w.setCurrentDocument(doc)

def help_about():
    import about
    about.AboutDialog(None).exec_()


