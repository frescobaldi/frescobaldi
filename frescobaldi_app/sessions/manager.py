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
Per-MainWindow session manager
"""


from PyQt5.QtWidgets import QAction, QActionGroup

import actioncollection
import actioncollectionmanager
import plugin
import document
import icons
import util
import sessions
import signals


def get(mainwindow):
    """Returns the SessionManager for the specified MainWindow."""
    return SessionManager.instance(mainwindow)


class SessionManager(plugin.MainWindowPlugin):
    """Per-MainWindow session manager.

    Emits the saveSessionData(name) signal when a session wants to be saved.
    Connect to this if you only want the notification for the current MainWindow
    (the one the user initiated the action from).

    Use app.saveSessionData(name) if you want to get the global notification.

    """

    # This signal is emitted when a session wants to save its data.
    saveSessionData = signals.Signal() # Session name

    def __init__(self, mainwindow):
        self.actionCollection = ac = SessionActions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.session_new.triggered.connect(self.newSession)
        ac.session_save.triggered.connect(self.saveSession)
        ac.session_manage.triggered.connect(self.manageSessions)
        ac.session_none.triggered.connect(self.noSession)

    def newSession(self):
        from . import dialog
        name = dialog.SessionEditor(self.mainwindow()).edit()
        if name:
            sessions.setCurrentSession(name)
            self.saveCurrentSession()

    def saveSession(self):
        if not sessions.currentSession():
            return self.newSession()
        self.saveCurrentSession()

    def manageSessions(self):
        from . import dialog
        dialog.SessionManagerDialog(self.mainwindow()).exec_()

    def noSession(self):
        if sessions.currentSession():
            self.saveCurrentSessionIfDesired()
            sessions.setCurrentSession(None)

    def startSession(self, name):
        """Switches to the given session."""
        if name == sessions.currentSession():
            return
        if self.mainwindow().queryClose():
            active = sessions.loadSession(name)
            if active:
                self.mainwindow().setCurrentDocument(active)
            else:
                self.mainwindow().cleanStart()

    def saveCurrentSessionIfDesired(self):
        """Saves the current session if it is configured to save itself on exit."""
        cur = sessions.currentSession()
        if cur:
            s = sessions.sessionGroup(cur)
            if s.value("autosave", True, bool):
                self.saveCurrentSession()

    def saveCurrentSession(self):
        """Saves the current session."""
        cur = sessions.currentSession()
        if cur:
            documents = self.mainwindow().documents()
            active = self.mainwindow().currentDocument()
            sessions.saveSession(cur, documents, active)
            self.saveSessionData(cur)


class SessionActions(actioncollection.ActionCollection):
    name = "session"
    def createActions(self, parent=None):
        self.session_new = QAction(parent)
        self.session_save = QAction(parent)
        self.session_manage = QAction(parent)
        self.session_none = QAction(parent)
        self.session_none.setCheckable(True)

        self.session_new.setIcon(icons.get('document-new'))
        self.session_save.setIcon(icons.get('document-save'))
        self.session_manage.setIcon(icons.get('view-choose'))

    def translateUI(self):
        self.session_new.setText(_("New Session", "&New..."))
        self.session_save.setText(_("&Save"))
        self.session_manage.setText(_("&Manage..."))
        self.session_none.setText(_("No Session"))


