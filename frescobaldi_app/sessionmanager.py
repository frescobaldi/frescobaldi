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
Named session support (not to be confused with the QSessionManager support
(see session.py)

A session is a global list of open documents, with some additional preferences set.

"""

import itertools
import weakref

from PyQt4.QtCore import QSettings, QUrl
from PyQt4.QtGui import QAction, QActionGroup

import app
import actioncollection
import document
import icons
import util


_currentSession = None


@app.qApp.aboutToQuit.connect
def _saveLastUsedSession():
    s = QSettings()
    s.beginGroup("session")
    s.setValue("lastused", _currentSession or "")
    
def loadDefaultSession():
    """Load the session which should be started by default.
    
    This can be:
    - no session,
    - last used session,
    - a specific session.
    
    Returns the document that should be set active (if any).
    """
    s = QSettings()
    s.beginGroup("session")
    start = s.value("startup", "none")
    name = None
    if start == "lastused":
        name = s.value("lastused", "")
    elif start == "custom":
        name = s.value("custom", "")
        if name not in sessionNames():
            s.setValue("startup", "none")
    if name and name in sessionNames():
        return loadSession(name)

def sessionGroup(name):
    """Returns the session settings group where settings can be stored for the named session.
    
    If the group doesn't exist, it is created.
    
    """
    session = app.settings("sessions")
    childGroups = session.childGroups()
    for group in childGroups:
        if session.value(group + "/name") == name:
            break
    else:
        for count in itertools.count(1):
            group = "session{0}".format(count)
            if group not in childGroups:
                session.setValue(group +  "/name", name)
                break
    session.beginGroup(group)
    return session

def sessionNames():
    session = app.settings("sessions")
    names = [session.value(group + "/name", "") for group in session.childGroups()]
    names.sort(key=util.naturalsort)
    return names
    
def loadSession(name):
    """Loads the given session (without closing other docs first)."""
    session = sessionGroup(name)
    
    urls = []
    for url in session.value("urls", []) or []:
        if isinstance(url, QUrl):
            urls.append(url)
    active = int(session.value("active", -1))
    result = None
    if urls:
        docs = [app.openUrl(url) for url in urls]
        if active not in range(len(docs)):
            active = 0
        result = docs[active]
    setCurrentSession(name)
    return result

def saveSession(name, documents, activeDocument=None):
    """Saves the list of documents and which one is active."""
    session = sessionGroup(name)
    session.setValue("urls", [doc.url() for doc in documents if not doc.url().isEmpty()])
    if activeDocument in documents:
        session.setValue("active", documents.index(activeDocument))
    else:
        session.remove("active")

def deleteSession(name):
    session = app.settings("sessions")
    for group in session.childGroups():
        if session.value(group + "/name", "") == name:
            session.remove(group)
            break
    if name == _currentSession:
        setCurrentSession(None)

def renameSession(old, new):
    """Renames a session."""
    session = sessionGroup(old)
    session.setValue("name", new)
    if old == currentSession():
        setCurrentSession(new)
    
def currentSession():
    return _currentSession
    
def setCurrentSession(name):
    global _currentSession
    if name != _currentSession:
        name and sessionGroup(name) # just select it, so its name is written in case it doesn't exist
        _currentSession = name
        app.sessionChanged()

def currentSessionGroup():
    """Returns the session settings at the current group is there is a current session.
    
    If there is no current session, returns None.
    
    """
    if _currentSession:
        return sessionGroup(_currentSession)


class SessionManager(object):
    def __init__(self, mainwindow):
        self.mainwindow = weakref.ref(mainwindow)
        
        self.createActions()
        
    def createActions(self):
        self.actionCollection = ac = SessionActions()
        ac.session_new.triggered.connect(self.newSession)
        ac.session_save.triggered.connect(self.saveSession)
        ac.session_manage.triggered.connect(self.manageSessions)
        
        # sessions menu
        self._sessionsActionGroup = ag = QActionGroup(self.mainwindow())
        ag.setExclusive(True)
        ag.addAction(ac.session_none)
        ag.triggered.connect(self.slotSessionsAction)
        
    def populateSessionsMenu(self):
        menu = self.mainwindow().menu_sessions
        ag = self._sessionsActionGroup
        for a in ag.actions():
            if a is not self.actionCollection.session_none:
                menu.removeAction(a)
                ag.removeAction(a)
        self.actionCollection.session_none.setChecked(not currentSession())
        for name in sessionNames():
            a = menu.addAction(name.replace('&', '&&'))
            a.setCheckable(True)
            if name == currentSession():
                a.setChecked(True)
            a.setObjectName(name)
            ag.addAction(a)
    
    def slotSessionsAction(self, action):
        if action is self.actionCollection.session_none:
            self.noSession()
        elif action.objectName() in sessionNames():
            self.startSession(action.objectName())
            
    def newSession(self):
        import sessiondialog
        name = sessiondialog.SessionEditor(self.mainwindow()).edit()
        if name:
            setCurrentSession(name)
            self.saveCurrentSession()
    
    def saveSession(self):
        if not currentSession():
            return self.newSession()
        self.saveCurrentSession()
        
    def manageSessions(self):
        import sessiondialog
        sessiondialog.SessionManagerDialog(self.mainwindow()).exec_()

    def noSession(self):
        if currentSession():
            self.saveCurrentSessionIfDesired()
            setCurrentSession(None)
    
    def startSession(self, name):
        """Switches to the given session."""
        if name == currentSession():
            return
        self.saveCurrentSessionIfDesired()
        if self.mainwindow().queryClose():
            active = loadSession(name) or document.Document()
            self.mainwindow().setCurrentDocument(active)
        
    def saveCurrentSessionIfDesired(self):
        """Saves the current session if it is configured to save itself on exit."""
        cur = currentSession()
        if cur:
            s = sessionGroup(cur)
            if s.value("autosave", True) not in (False, 'false'):
                self.saveCurrentSession()
    
    def saveCurrentSession(self):
        """Saves the current session."""
        cur = currentSession()
        if cur:
            documents = self.mainwindow().documents()
            active = self.mainwindow().currentDocument()
            saveSession(cur, documents, active)


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
        

