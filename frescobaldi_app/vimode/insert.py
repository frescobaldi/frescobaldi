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
Insert ViMode.
"""


from PyQt5.QtCore import Qt

from . import handlerbase


class InsertMode(handlerbase.Handler):

    def enter(self):
        m = self.vimode
        m.textEdit().setCursorWidth(m._originalCursorWidth)
        m.clearCursor()

    def handleKeyPress(self, ev):
        if ev.key() == Qt.Key_Escape and ev.modifiers() == Qt.NoModifier:
            self.setNormalMode()
            return True

