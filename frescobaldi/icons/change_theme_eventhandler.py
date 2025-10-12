# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
This handles the QEvent::ApplicationPaletteChange event type sent to the QApplication when
the theme (Dark or Light) is changed.

"""
import platform

from PyQt6.QtCore import QEvent, QObject, QSettings

import app, icons


handler = None


def initialize():
    global handler
    handler = ChangingThemeEventHandler()
    app.qApp.installEventFilter(handler)


class ChangingThemeEventHandler(QObject):
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.ApplicationPaletteChange:
            s = QSettings()
            if s.value("system_icons", True, bool):
                icons.update_theme()
            return True
        return False


