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

If this script is called directly instead of imported,
it discards the session information given as the argument.

If this script is imported, it connects the saveState and commitData functions
to the QApplication signals.

"""

from __future__ import unicode_literals

import os
import sys

from PyQt4.QtCore import QObject, QSettings, Qt, SIGNAL
from PyQt4.QtGui import QApplication, QSessionManager

import info
import app

def sessionSettings():
    """Returns the QSettings object for sessiondata."""
    settings = QSettings()
    settings.beginGroup("sessiondata")
    return settings


if __name__ == '__main__':
    settings = sessionSettings()
    settings.remove(sys.argv[-1])
    sys.exit(0)


### Continued here if normally imported

import mainwindow

def sessionKey():
    """ Returns the full session key. """
    return '{0}_{1}'.format(app.qApp.sessionId(), app.qApp.sessionKey())

def saveState(sm):
    """Save session state on behalf of the session manager."""
    sm.setRestartHint(QSessionManager.RestartIfRunning)

    key = sessionKey()
    restartCommand = [sys.executable, os.path.abspath(sys.argv[0]), '-session', key]
    sm.setRestartCommand(restartCommand)
    
    discardCommand = [sys.executable, __file__, key]
    sm.setDiscardCommand(discardCommand)

def commitData(sm):
    """Save a session on behalf of the session manager."""
    if not sm.allowsInteraction():
        pass # TODO: can implement saving unsaved/unnamed docs to cache buffers
    sm.release()
    saveState(sm)
    settings = sessionSettings()
    settings.beginGroup(sessionKey())
    settings.setValue('numwindows', len(app.windows))
    for index, win in enumerate(app.windows):
        settings.beginGroup("mainwindow{0}".format(index))
        win.writeSessionSettings(settings)
        settings.endGroup()
    settings.endGroup()
    settings.sync()

def restoreSession():
    """Restore a session saved by the session manager."""
    settings = sessionSettings()
    settings.beginGroup(sessionKey())
    for index in range(settings.value('numwindows', 0, int)):
        settings.beginGroup("mainwindow{0}".format(index))
        win = mainwindow.MainWindow()
        win.readSessionSettings(settings)
        win.show()
        settings.endGroup()
    settings.endGroup()

# the new-style way of connecting fails on PyQt4 4.8.x...
QObject.connect(app.qApp, SIGNAL("saveStateRequest(QSessionManager&)"), saveState)
QObject.connect(app.qApp, SIGNAL("commitDataRequest(QSessionManager&)"), commitData)
