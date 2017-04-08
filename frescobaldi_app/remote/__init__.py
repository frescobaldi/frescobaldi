# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2012 - 2014 by Wilbert Berendsen
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
Inter-Process Communication with already running Frescobaldi instances.
"""


import os
import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

import app
import appinfo


_server = None


def get():
    """Return a remote Frescobaldi, or None if not available."""
    socket = QLocalSocket()
    name = os.environ.get("FRESCOBALDI_SOCKET")
    for name in (name,) if name else ids():
        socket.connectToServer(name)
        if socket.waitForConnected(5000):
            from . import api
            return api.Remote(socket)


def init():
    """Start listening to incoming connections."""
    global _server
    if _server is not None:
        return

    server = QLocalServer(None)

    # find a free socket name to use
    for name in ids():
        if server.listen(name):
            break
    else:
        # all names failed, try to contact and remove stale file if that fails
        socket = QLocalSocket()
        for name in ids():
            socket.connectToServer(name)
            if not socket.waitForConnected(10000):
                QLocalServer.removeServer(name)
                if server.listen(name):
                    break
            else:
                socket.disconnectFromServer()
        else:
            # no ids left, don't listen
            return
    app.aboutToQuit.connect(server.close)
    server.newConnection.connect(slot_new_connection)
    os.environ["FRESCOBALDI_SOCKET"] = name
    _server = server


def quit():
    """Stop listening to incoming connections."""
    global _server
    if _server is not None:
        _server.close()
        _server = None


def slot_new_connection():
    """Called when someone connects to the server socket."""
    from . import api
    api.Incoming(_server.nextPendingConnection())


def ids(count=3):
    """Yield at most count (default 3) names to use for the IPC socket."""
    i = generate_id()
    yield i
    for c in range(1, count):
        yield '{0}#{1}'.format(i, c)


def generate_id():
    """Generate a name for the IPC socket.

    The name is unique for the application, the user id and the DISPLAY
    on X11.

    """
    name = [appinfo.name]

    try:
        name.append(format(os.getuid()))
    except AttributeError:
        pass

    display = os.environ.get("DISPLAY")
    if display:
        name.append(display.replace(':', '_').replace('/', '_'))

    return '-'.join(name)


def enabled():
    """Return whether remote support is enabled.

    By default it is enabled.

    """
    return QSettings().value('allow_remote', True, bool)


def setup():
    """Enable or disable the remote server according to settings."""
    init() if enabled() else quit()

app.settingsChanged.connect(setup)

