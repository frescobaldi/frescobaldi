# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2016 - 2016 by Wilbert Berendsen
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
Simple eventfilter that alters the behaviour of the horizontal arrow keys
to not go to the next or previous block.
"""

from PyQt5.QtCore import QEvent, QObject, QSettings
from PyQt5.QtGui import QKeySequence


import app


def handle(edit, ev):
    """Return True if an horizontal arrow key press event was handled.
    
    edit: Q(Plain)TextEdit instance
    ev: the KeyPress QEvent
    
    """
    if ev == QKeySequence.MoveToNextChar or ev == QKeySequence.SelectNextChar:
        return edit.textCursor().atBlockEnd()
    elif ev == QKeySequence.MoveToPreviousChar or ev == QKeySequence.SelectPreviousChar:
        return edit.textCursor().atBlockStart()
    return False


class Handler(QObject):
    handle = False
    def eventFilter(self, obj, ev):
        if self.handle and ev.type() == QEvent.KeyPress:
            return handle(obj, ev)
        return False


handler = Handler()


def _setup():
    handler.handle = QSettings().value("view_preferences/keep_cursor_in_line", False, bool)

app.settingsChanged.connect(_setup)
_setup()
