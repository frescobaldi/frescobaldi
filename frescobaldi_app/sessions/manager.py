# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

from PyQt4.QtGui import QAction, QActionGroup

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
    (the one the user initated the action from).
    
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
        
        # sessions menu
        self._sessionsActionGroup = ag = QActionGroup(mainwindow)
        ag.setExclusive(True)
        ag.addAction(ac.session_none)
        ag.triggered.connect(self.slotSessionsAction)
        
    def addActionsToMenu(self, m):
        """Adds our actions to the sessions menu."""
        ac = self.actionCollection
        m.addAction(ac.session_new)
        m.addAction(ac.session_save)
        m.addSeparator()
        m.addAction(ac.session_manage)
        m.addSeparator()
        m.addAction(ac.session_none)
        m.addSeparator()
        m.aboutToShow.connect(self.populateSessionsMenu)
    
    def populateSessionsMenu(self):
        menu = self.mainwindow().menu_sessions
        ag = self._sessionsActionGroup
        for a in ag.actions():
            if a is not self.actionCollection.session_none:
                menu.removeAction(a)
                ag.removeAction(a)
        self.actionCollection.session_none.setChecked(not sessions.currentSession())
        for name in sessions.sessionNames():
            a = menu.addAction(name.replace('&', '&&'))
            a.setCheckable(True)
            if name == sessions.currentSession():
                a.setChecked(True)
            a.setObjectName(name)
            ag.addAction(a)
        util.addAccelerators(menu.actions())
    
    def slotSessionsAction(self, action):
        if action is self.actionCollection.session_none:
            self.noSession()
        elif action.objectName() in sessions.sessionNames():
            self.startSession(action.objectName())
            
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
        self.saveCurrentSessionIfDesired()
        if self.mainwindow().queryClose():
            active = sessions.loadSession(name) or document.Document()
            self.mainwindow().setCurrentDocument(active)
        
    def saveCurrentSessionIfDesired(self):
        """Saves the current session if it is configured to save itself on exit."""
        cur = sessions.currentSession()
        if cur:
            s = sessions.sessionGroup(cur)
            if s.value("autosave", True) not in (False, 'false'):
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
        self.session_new.setText(_("&New..."))
        self.session_save.setText(_("&Save"))
        self.session_manage.setText(_("&Manage..."))
        self.session_none.setText(_("No Session"))


