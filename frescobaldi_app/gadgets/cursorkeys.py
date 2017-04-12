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
Simple event filter that alters the behaviour of cursor-moving keys in a text
edit (QTextEdit or QPlainTextEdit).
"""

from PyQt5.QtCore import QEvent, QObject, QSettings
from PyQt5.QtGui import QKeySequence, QTextCursor


class KeyPressHandler(QObject):
    """Handles various keypress events in a configurable way.

    Instance attributes (default at class level):

    handle_home (False):    handles the Home/Shift Home keys so that initial
                            whitespace is skipped

    handle_horizontal (False): don't move to the previous or next
                            block when using the horizontal arrow keys

    handle_vertical (False): go to the end of a block when Down or PageDown
                            is pressed in the last block, or Up or PageUp in the
                            first block.

    """

    # special home/shift home behaviour
    handle_home = False

    # stay in block on horizontal arrow keys
    handle_horizontal = False

    # go to first character when Up or PgUp pressed in first block, or to
    # last character when Dn or PgDn is pressed in the last block.
    handle_vertical = False


    def eventFilter(self, obj, ev):
        """Reimplemented to dispatch keypress events to the handle() method."""
        if ev.type() == QEvent.KeyPress:
            return self.handle(obj, ev)
        return False

    def handle(self, edit, ev):
        """Return True or False, handling the event if applicable.

        This method is called by eventFilter() for KeyPress events.

        edit: Q(Plain)TextEdit instance
        ev: the KeyPress QEvent

        """
        result = None
        if self.handle_home:
            result = self.handleHome(edit, ev)
        if result is None and self.handle_horizontal:
            result = self.handleHorizontal(edit, ev)
        if result is None and self.handle_vertical:
            result = self.handleVertical(edit, ev)

        return bool(result) # None becomes False

    def handleHome(self, edit, ev):
        """Return None, False or True.

        None when Home was not pressed,
        True when the event was handled,
        False when the event was not handled and should be handled normally.

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

    def handleHorizontal(self, edit, ev):
        """Return None, False or True.

        None when no horizontal arrow key was pressed,
        True when the event was handled,
        False when the event was not handled and should be handled normally.

        """
        if ev == QKeySequence.MoveToNextChar or ev == QKeySequence.SelectNextChar:
            return edit.textCursor().atBlockEnd()
        elif ev == QKeySequence.MoveToPreviousChar or ev == QKeySequence.SelectPreviousChar:
            return edit.textCursor().atBlockStart()

    def handleVertical(self, edit, ev):
        """Return None, False or True.

        None when no horizontal arrow key was pressed,
        True when the event was handled,
        False when the event was not handled and should be handled normally.

        """
        cursor = edit.textCursor()
        pos = cursor.position()
        if ev == QKeySequence.MoveToPreviousLine or ev == QKeySequence.MoveToPreviousPage:
            cursor.movePosition(QTextCursor.Up)
            if cursor.position() == pos:    # no move
                cursor.movePosition(QTextCursor.Start)
                edit.setTextCursor(cursor)
                return True
            return False
        elif ev == QKeySequence.SelectPreviousLine or ev == QKeySequence.SelectPreviousPage:
            cursor.movePosition(QTextCursor.Up, QTextCursor.KeepAnchor)
            if cursor.position() == pos:    # no move
                cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
                edit.setTextCursor(cursor)
                return True
            return False
        elif ev == QKeySequence.MoveToNextLine or ev == QKeySequence.MoveToNextPage:
            cursor.movePosition(QTextCursor.Down)
            if cursor.position() == pos:    # no move
                cursor.movePosition(QTextCursor.End)
                edit.setTextCursor(cursor)
                return True
            return False
        elif ev == QKeySequence.SelectNextLine or ev == QKeySequence.SelectNextPage:
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)
            if cursor.position() == pos:    # no move
                cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                edit.setTextCursor(cursor)
                return True
            return False


