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
Stuff dealing with the QSessionManager.
"""


import os
import sys

from PyQt5.QtCore import QObject, QSettings, Qt, QUrl
from PyQt5.QtGui import QSessionManager
from PyQt5.QtWidgets import QApplication

import appinfo
import app
import mainwindow


def sessionSettings(key):
    """Returns the QSettings object for sessiondata of the specified key."""
    settings = QSettings()
    settings.beginGroup("sessiondata")
    settings.beginGroup(key)
    return settings


def commitData(sm):
    """Save a session on behalf of the session manager."""
    if not sm.allowsInteraction():
        pass # TODO: can implement saving unsaved/unnamed docs to cache buffers
    sm.release()
    key = sm.sessionKey()
    saveSession(key)


def saveSession(key):
    """Save the current session under key."""
    settings = sessionSettings(key)
    ## save current named session name
    import sessions
    settings.setValue('session_name', sessions.currentSession() or "")
    ## save the list of open documents
    settings.setValue('numdocuments', len(app.documents))
    for index, d in enumerate(app.documents):
        settings.beginGroup("document{0}".format(index))
        settings.setValue("url", d.url())
        settings.endGroup()
    ## save windows
    settings.setValue('numwindows', len(app.windows))
    for index, win in enumerate(app.windows):
        settings.beginGroup("mainwindow{0}".format(index))
        win.writeSessionSettings(settings)
        settings.setValue("active_document", win.currentDocument().url())
        settings.endGroup()
    settings.sync()


def restoreSession(key):
    """Restore a session specified by key, previously saved by the session manager."""
    settings = sessionSettings(key)
    ## restore current named session name
    session_name = settings.value('session_name', "", str)
    if session_name:
        import sessions
        sessions.setCurrentSession(session_name)
    ## restore documents
    numdocuments = settings.value('numdocuments', 0, int)
    doc = None
    for index in range(numdocuments):
        settings.beginGroup("document{0}".format(index))
        url = settings.value("url", QUrl(), QUrl)
        if url.isEmpty():
            import document
            doc = document.Document()
        else:
            try:
                doc = app.openUrl(url)
            except IOError:
                pass
        settings.endGroup()
    # open at least one
    if doc is None:
        doc = app.openUrl(QUrl())
    ## restore windows
    numwindows = settings.value('numwindows', 0, int)
    if numwindows > 0:
        for index in range(numwindows):
            settings.beginGroup("mainwindow{0}".format(index))
            win = mainwindow.MainWindow()
            win.readSessionSettings(settings)
            win.show()
            u = settings.value("active_document", QUrl(), QUrl)
            # we don't use app.findDocument because it does not allow empty url
            for d in app.documents:
                if u == d.url():
                    win.setCurrentDocument(d)
                    break
            else:
                win.setCurrentDocument(app.documents[0])
            settings.endGroup()
    else:
        win = mainwindow.MainWindow()
        win.show()


@app.oninit
def _setup():
    # the new-style way of connecting fails on PyQt5 4.8.x...
    app.qApp.commitDataRequest.connect(commitData)


