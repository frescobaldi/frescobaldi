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
Performs upgrades in the settings structure.
"""


from PyQt6.QtCore import QSettings

import appinfo

def update(version):
    """Call subroutines listed below for version upgrades."""

    if version < 1:
        moveSettingsToNewRoot()

    if version < 3:
        renameUseshebang()

    if version < 4:
        removeUseshebang()

    # ... add other setting updates here...



def moveSettingsToNewRoot():
    """Move all settings to one application file."""
    movelist = [[appinfo.name, appinfo.url, False], "metainfo", "snippets", "sessions", "sessiondata"]
    for moveitem in movelist:
        if isinstance(moveitem, str):
            moveitem = [moveitem, appinfo.name, True]
        o = QSettings(moveitem[1], moveitem[0])
        o.setFallbacksEnabled(False)
        keys = o.allKeys()
        if len(keys) > 0:
            s = QSettings()
            if moveitem[2]:
                s.beginGroup(moveitem[0])
            for k in keys:
                s.setValue(k, o.value(k))
            o.clear()

def renameUseshebang():
    s = QSettings()
    l = s.beginReadArray("lilypondinfo")
    old = []
    for i in range(l):
        s.setArrayIndex(i)
        old.append(s.value("always_use_shebang", None))
    s.endArray()
    s.beginWriteArray("lilypondinfo")
    for i in range(l):
        s.setArrayIndex(i)
        if old[i] is not None:
            s.setValue("useshebang", old[i])
            s.remove("always_use_shebang")
    s.endArray()

def removeUseshebang():
    s = QSettings()
    l = s.beginReadArray("lilypondinfo")
    s.endArray()
    s.beginWriteArray("lilypondinfo")
    for i in range(l):
        s.setArrayIndex(i)
        s.remove("useshebang")
    s.endArray()
