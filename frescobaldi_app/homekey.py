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
Simple eventfilter that makes Home and Shift+Home in text editor widgets
go to the first non-space character of a line, instead of the very beginning.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QEvent, QObject
from PyQt4.QtGui import QKeySequence, QTextCursor


def handle(edit, ev):
    """Returns True if a Home/Shift+Home key press event was handled.
    
    edit: Q(Plain)TextEdit instance
    ev: the KeyPress QEvent
    
    """
    home = ev == QKeySequence.MoveToStartOfLine
    s_home = ev == QKeySequence.SelectStartOfLine
    if home or s_home:
        # go to first non-space character if not already there
        cursor = edit.textCursor()
        text = cursor.block().text()
        pos = cursor.block().position() + len(text) - len(text.lstrip())
        if cursor.position() != pos:
            mode = QTextCursor.KeepAnchor if s_home else QTextCursor.MoveAnchor
            cursor.setPosition(pos, mode)
            edit.setTextCursor(cursor)
            return True
    return False


class Handler(QObject):
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.KeyPress:
            return handle(obj, ev)
        return False


handler = Handler()


