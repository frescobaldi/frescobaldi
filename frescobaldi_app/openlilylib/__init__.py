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
openLilyLib support

openLilylib (https://github.com/openlilylib) is a LilyPond extension package framework
intended to make additional functionality available for LilyPond users in
coherent "packages" without having to add the functionality to LilyPond's code base.

Support for openLilyLib in Frescobaldi serves two purposes:
- giving openLilyLib users convenient interfaces to manage and configure packages
  and ease their use in LilyPond projects
- adding "compilation features" similar to the Layout Control Mode
  by injecting openLilyLib code into the compilation.
  It is important to keep in mind that such functions must *not* persistently change
  the documents and make them work within Frescobaldi only.
"""

import os
import sys

from PyQt5.QtCore import (
    QObject,
    QSettings
)

import app

class OllLib(QObject):
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
                packages[d] = OllPackage(self, os.path.join(root, d))
            except:
                # ignore directories that don't contain a valid openLilyLib package
                continue
        self._packages = packages

    def valid(self, root = None):
        """Return True if a valid openLilyLib installation is found,
        either in self._root or in the given path"""
        if self._valid is None:
            path = root if root else self.root()
            try:
                OllPackage(self, os.path.join(path, 'oll-core'))
                self._valid = True
            except Exception as e:
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


class OLLException(Exception):
    pass

class OllPackage(QObject):
    def __init__(self, lib, root):
        self.lib = lib
        self.root = root
        self.name = os.path.basename(root)
        self.parseConfig()
        self.icon = True if 'icon.svg' in os.listdir(root) else False

    def parseConfig(self):
        """
        Parse a package's configuration file.
        Raises an exception if anything goes wrong.
        """

        # import vbcl from within oll-core
        #TODO: Handle reloading when root has changed
        import vbcl
        # try to parse configuration file.
        # May raise an exception when no 'package.cnf' is found
        cfg_dict = vbcl.parse_file(os.path.join(self.root, 'package.cnf'))
        self.displayName = cfg_dict['display-name']
        self.shortDescription = cfg_dict['short-description']
        self.description = cfg_dict['description']
        self.dependencies = cfg_dict['dependencies']
        self.oll_core_version = cfg_dict['oll-core']
        self.maintainers = cfg_dict['maintainers']
        self.version = cfg_dict['version']
        self.license = cfg_dict['license']


# cached object to access by openlilylib.lib
lib = OllLib()
