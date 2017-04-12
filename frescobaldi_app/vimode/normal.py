# vimode -- Vi Mode package for QPlainTextEdit
#
# Copyright (c) 2012 by Wilbert Berendsen
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
Normal ViMode.
"""


import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor

from . import handlerbase

commands = []


class NormalMode(handlerbase.Handler):
    def __init__(self, vimode):
        super(NormalMode, self).__init__(vimode)
        self._command = []
        self._count = 0

    def enter(self):
        self.vimode.textEdit().setCursorWidth(0)

    def updateCursorPosition(self):
        cursor = self.textCursor()
        if cursor.hasSelection() and cursor.position() > cursor.anchor():
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
        else:
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        self.vimode.drawCursor(cursor)

    def handleKeyPress(self, ev):
        # is a number being entered?
        if not self._command and Qt.Key_0 <= ev.key() <= Qt.Key_9:
            self._count *= 10
            self._count += ev.key() - Qt.Key_0
            return True
        # backspace?
        if ev.key() == Qt.Key_Backspace:
            if self._command:
                # remove last key typed
                del self._command[-1]
            else:
                self._count = 0
            return True

        # TEMP
        if ev.text():
            self._command.append(ev.text())

        cmd = ''.join(self._command)
        for s, f in commands:
            if re.compile(s).match(cmd):
                f(self)
                self._count = 0
                self._command = []
                return True

        return True


    def command(cmds, count=True, set_cursor=True):
        def decorator(func):
            def wrapper(self):
                cursor = self.textCursor()
                if count:
                    for i in range(max(1, self._count)):
                        func(self, cursor)
                else:
                    func(self, cursor)
                if set_cursor:
                    self.setTextCursor(cursor)
            for c in cmds:
                commands.append((c, wrapper))
        return decorator

    @command(['h', '<left>'])
    def move_left(self, cursor):
        if cursor.position() > cursor.block().position():
            cursor.movePosition(QTextCursor.PreviousCharacter)

    @command(['l', '<right>'])
    def move_right(self, cursor):
        if cursor.position() < cursor.block().position() + cursor.block().length() - 2:
            cursor.movePosition(QTextCursor.NextCharacter)

    @command('i', set_cursor=False)
    def insert_mode(self, cursor):
        self.setInsertMode()




