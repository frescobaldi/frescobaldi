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
"""



from PyQt4.QtCore import *

import app


_currentSession = None


def loadDefaultSession():
    """Finds out which session should be started by default.
    
    This can be:
    - no session,
    - last used session,
    - a specific session.
    
    Returns the document that should be set active (if any).
    """
    s = QSettings()
    s.beginGroup("Session")
    start = s.value("startup", "none")
    name = None
    if start == "lastused":
        name = s.value("lastused", "")
    elif start == "custom":
        name = s.value("custom", "")
    if name:
        return loadSession(name)

def sessionGroup(name):
    """Returns the session settings group where settings can be stored for the named session."""
    session = app.settings("sessions")
    session.beginGroup(name)
    return session
    
def loadSession(name):
    global _currentSession
    _currentSession = name
    session = sessionGroup(name)
    
    urls = []
    for url in session.value("urls", []) or []:
        if isinstance(url, QUrl):
            urls.append(url)
    active = QUrl(session.value("active", QUrl()))
    result = None
    if urls:
        try:
            index = urls.index(active)
        except ValueError:
            index = 0
        docs = [app.openUrl(url) for url in urls]
        result = docs[index]
    app.sessionChanged()
    return result

def currentSession():
    return _currentSession
    


