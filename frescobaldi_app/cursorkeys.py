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
Configurable cursor keys behaviour.

Install the global handler as an event filter for a Q(Plain)TextEdit.

"""

from PyQt5.QtCore import QSettings


import app
import gadgets.cursorkeys


# global handler
handler = gadgets.cursorkeys.KeyPressHandler()



def _setup():
    s = QSettings()
    s.beginGroup("view_preferences")
    handler.handle_home = s.value("smart_home_key", True, bool)
    handler.handle_horizontal = s.value("keep_cursor_in_line", False, bool)
    handler.handle_vertical = s.value("smart_start_end", True, bool)

app.settingsChanged.connect(_setup)
_setup()
