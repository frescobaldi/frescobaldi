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
Backup files before overwriting
"""


import os
import shutil

from PyQt5.QtCore import QSettings


def backup(filename):
    """Makes a backup of 'filename'.

    Returns True if the backup succeeded.

    """
    if filename:
        try:
            shutil.copy(filename, backupName(filename))
            return True
        except (IOError, OSError):
            pass
    return False


def removeBackup(filename):
    """Removes filename's backup unless the user has configured to keep it."""
    if filename and not QSettings().value("backup_keep", False, bool):
        try:
            os.remove(backupName(filename))
        except (IOError, OSError):
            pass


def scheme():
    """Returns a string that must contain "FILE".

    Replacing that part yields the backup name.

    """
    s = QSettings().value("backup_scheme", "FILE~")
    assert 'FILE' in s and s != 'FILE'
    return s


def backupName(filename):
    """Returns the backup file name for the given filename."""
    return scheme().replace("FILE", filename)


