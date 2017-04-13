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
Sets the user interface style.
"""



from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QStyleFactory

import app

_system_default = None # becomes app.qApp.style().objectName()


def keys():
    return [name.lower() for name in QStyleFactory.keys()]


def setStyle():
    global _system_default

    style = QSettings().value("guistyle", "", str).lower()
    if style not in keys():
        style = _system_default
    if style != app.qApp.style().objectName():
        app.qApp.setStyle(QStyleFactory.create(style))

@app.oninit
def initialize():
    """Initializes the GUI style setup. Called op app startup."""
    global _system_default

    _system_default = app.qApp.style().objectName()
    app.settingsChanged.connect(setStyle)
    setStyle()

