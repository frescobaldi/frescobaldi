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
openLilyLib main library
"""

import os
import sys

from PyQt5.QtCore import (
    QObject,
    QSettings
)

import app
from . import package

class OllLib(QObject):
    """Class representing the openLilyLib library as a whole"""
    def __init__(self):
        self._root = None
        self._packages = None
        self._valid = None
        app.settingsChanged.connect(self.saveSettings)

    def invalidate(self):
        """Invalidate cache"""
        self._root = None
        self._packages = None
        self._valid = None

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("openlilylib_settings")
        self.setRoot(s.value("oll-root", '', str))

    def saveSettings(self):
        QSettings().setValue('openlilylib_settings/oll-root', self._root)
        self.invalidate()

    def _read_packages(self):
        """Read all subdirectories and try to load them as OLL packages"""
        root = self.root()
        if not root or not self.valid():
            self._packages = {}
            return
        packages = {}
        dirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        for d in dirs:
            try:
                packages[d] = package.OllPackage(self, os.path.join(root, d))
            except Exception as e:
                # ignore directories that don't contain a valid openLilyLib package
                # Keep this around because we'll often need this while developing
                print(e)
                continue
        self._packages = packages

    def valid(self, root = None):
        """Return True if a valid openLilyLib installation is found,
        either in self._root or in the given path"""
        if self._valid is None:
            path = root if root else self.root()
            try:
                package.OllPackage(self, os.path.join(path, 'oll-core'))
                self._valid = True
            except Exception as e:
                print(e)
                self._valid = False
        return self._valid

    def packages(self):
        """Return (cached) dictionary with packages"""
        if self._packages is None:
            self._read_packages()
        return self._packages

    def root(self):
        """Return (cached) openLilyLib root directory"""
        if self._root is None:
            self.loadSettings()
        return self._root

    def setRoot(self, root, mustExist = False):
        """
        Change the openLilyLib root directory.
        Handle module path for including vbcl from within oll-core.
        Invalidate cached properties.
        """
        if root == self._root:
            return
        if self._root is not None:
            vbcl_dir_old = os.path.join(self._root, 'oll-core', 'py')
            sys.path.remove(vbcl_dir_old)
        vbcl_dir_new = os.path.join(root, 'oll-core', 'py')
        sys.path.append(vbcl_dir_new)
        if mustExist and not self.valid(root):
            raise Exception(_("No valid openLilyLib installation found in {}".format(root)))
        self.invalidate()
        self._root = root

