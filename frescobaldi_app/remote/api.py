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

This is done via a local (unix domain) socket, to which simple commands
are written. Every command is a line of ASCII characters, terminated by a
newline. Arguments are separated with spaces.
"""


from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QLocalSocket

import app


_incoming_handlers = []


class Remote(object):
    """Speak to the remote Frescobaldi."""
    def __init__(self, socket):
        self.socket = socket

    def close(self):
        """Close and disconnect."""
        self.write(b'bye\n')
        self.socket.waitForBytesWritten()
        self.socket.disconnectFromServer()
        if self.socket.state() == QLocalSocket.ConnectedState:
            self.socket.waitForDisconnected(5000)

    def write(self, data):
        """Writes binary data."""
        while data:
            l = self.socket.write(data)
            data = data[l:]

    def command_line(self, args, urls):
        """Let remote Frescobaldi handle a command line."""
        if urls:
            if args.encoding:
                self.write('encoding {0}\n'.format(args.encoding).encode('utf-8'))
            for u in urls:
                self.write(b'open ' + u.toEncoded() + b'\n')
            self.write(b'set_current ' + u.toEncoded() + b'\n')
            if args.line is not None:
                self.write('set_cursor {0} {1}\n'.format(args.line, args.column).encode('utf-8'))
        self.write(b'activate_window\n')


class Incoming(object):
    """Handle an incoming connection."""
    def __init__(self, socket):
        """Start reading from the socket and perform the commands."""
        self.socket = socket
        self.data = bytearray()
        self.encoding = None
        _incoming_handlers.append(self)
        socket.readyRead.connect(self.read)

    def close(self):
        if self in _incoming_handlers:
            self.socket.deleteLater()
            _incoming_handlers.remove(self)

    def read(self):
        """Read from the socket and let command() handle the commands."""
        self.data.extend(self.socket.readAll())
        pos = self.data.find(b'\n')
        end = 0
        while pos != -1:
            self.command(self.data[end:pos])
            end = pos + 1
            pos = self.data.find(b'\n', end)
        del self.data[:end]
        if self.socket.state() == QLocalSocket.UnconnectedState:
            self.close()

    def command(self, command):
        """Perform one command."""
        command = command.split()
        cmd = command[0]
        args = command[1:]

        win = app.activeWindow()
        if not win:
            import mainwindow
            win = mainwindow.MainWindow()
            win.show()

        if cmd == b'open':
            url = QUrl.fromEncoded(args[0])
            win.openUrl(url, self.encoding)

        elif cmd == b'encoding':
            self.encoding = str(args[0])
        elif cmd == b'activate_window':
            win.activateWindow()
            win.raise_()
        elif cmd == b'set_current':
            url = QUrl.fromEncoded(args[0])
            try:
                win.setCurrentDocument(app.openUrl(url)) # already loaded
            except IOError:
                pass
        elif cmd == b'set_cursor':
            line, column = map(int, args)
            cursor = win.textCursor()
            pos = cursor.document().findBlockByNumber(line - 1).position() + column
            cursor.setPosition(pos)
            win.currentView().setTextCursor(cursor)
        elif cmd == b'bye':
            self.close()


