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
Named session support (not to be confused with the QSessionManager support
in session.py)

A session is a global list of open documents, with some additional preferences set.

"""


import itertools

from PyQt5.QtCore import QSettings, QUrl

import app
import util
import qsettings


_currentSession = None


@app.mainwindowClosed.connect
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
    start = s.value("startup", "none", str)
    name = None
    if start == "lastused":
        name = s.value("lastused", "", str)
    elif start == "custom":
        name = s.value("custom", "", str)
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
        if session.value(group + "/name", "", str) == name:
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
    names = [session.value(group + "/name", "", str) for group in session.childGroups()]
    names.sort(key=util.naturalsort)
    return names

def loadSession(name):
    """Loads the given session (without closing other docs first).

    Return the document that should become the active one.
    If None is returned, the session did not open any documents!

    """
    session = sessionGroup(name)
    urls = qsettings.get_url_list(session, "urls")
    active = session.value("active", -1, int)
    result = None
    docs = []
    for url in urls:
        try:
            doc = app.openUrl(url)
        except IOError:
            pass
        else:
            docs.append(doc)
    setCurrentSession(name)
    if docs:
        if active not in range(len(docs)):
            active = 0
        return docs[active]

def saveSession(name, documents, activeDocument=None):
    """Saves the list of documents and which one is active."""
    # only save the documents that have an url
    documents = [doc for doc in documents if not doc.url().isEmpty()]
    session = sessionGroup(name)
    session.setValue("urls", [doc.url() for doc in documents])
    if activeDocument in documents:
        session.setValue("active", documents.index(activeDocument))
    else:
        session.remove("active")
    app.saveSessionData(name)

def deleteSession(name):
    session = app.settings("sessions")
    for group in session.childGroups():
        if session.value(group + "/name", "", str) == name:
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
        app.sessionChanged(name)

def currentSessionGroup():
    """Returns the session settings at the current group is there is a current session.

    If there is no current session, returns None.

    """
    if _currentSession:
        return sessionGroup(_currentSession)


