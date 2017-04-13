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
This is only imported on Mac OS X, from main.py.

It initializes various stuff that's only relevant on Mac OS X.

"""


from PyQt5.QtCore import QTimer

import app

@app.mainwindowClosed.connect
def check_open_window():
    if not app.windows:
        from . import globalmenu
        QTimer.singleShot(0, globalmenu.setup)

def initialize():
    # on Mac OS X, handle FileOpen requests (e.g. double-clicking a file in the
    # Finder), these events also can occur right on application start.
    # We do this just before creating the window, so that when multiple files
    # are opened on startup (I don't know whether that really could happen),
    # they are not made the current document, as that slows down loading
    # multiple documents drastically.
    from . import file_open_eventhandler
    file_open_eventhandler.initialize()

    # handle window icon drag events
    from . import icon_drag_eventhandler
    icon_drag_eventhandler.initialize()

    # on mac os, the app should remain running, even if there is no main window
    # anymore. In this case, we setup a basic global menu.
    app.qApp.setQuitOnLastWindowClosed(False)

