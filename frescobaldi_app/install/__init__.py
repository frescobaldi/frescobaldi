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
Checks for upgrades in the settings structure.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings

# increase this number by one whenever something needs to be done, installed
# or updated concerning the application settings.
SETTINGS_VERSION = 1

version = QSettings().value("settings_version", 0, int)

if version != SETTINGS_VERSION:
    from . import update
    update.update(version)
    
    #uncomment next lines when the upgrade from 0 to 1 works
    QSettings().setValue("settings_version", SETTINGS_VERSION)
    QSettings().sync() # just to be sure

