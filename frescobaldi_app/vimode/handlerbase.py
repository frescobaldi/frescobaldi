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
Base class for mode handlers.
"""


from . import NORMAL, VISUAL, INSERT, REPLACE


class Handler(object):
    def __init__(self, vimode):
        self.vimode = vimode

    def enter(self):
        """Called when the mode is entered."""

    def leave(self):
        """Called when the mode is left."""

    def textCursor(self):
        """Returns the text cursor of the Q(Plain)TextEdit."""
        return self.vimode.textEdit().textCursor()

    def setTextCursor(self, cursor):
        """Sets the text cursor of the Q(Plain)TextEdit."""
        self.vimode.textEdit().setTextCursor(cursor)

    def handleKeyPress(self, ev):
        """Called when a key is pressed in this mode.

        Should return True if the keypress is not to be handled anymore
        by the widget.

        """

    def updateCursorPosition(self):
        """Should redraw the cursor position."""

    def setNormalMode(self):
        self.vimode.setMode(NORMAL)

    def setVisualMode(self):
        self.vimode.setMode(VISUAL)

    def setInsertMode(self):
        self.vimode.setMode(INSERT)

    def setReplaceMode(self):
        self.vimode.setMode(REPLACE)


