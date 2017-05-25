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
openLilyLib package support
"""

import os
import re

from PyQt5.QtCore import (
    QObject
)
from PyQt5.QtGui import QIcon

import icons

class OllPackage(QObject):
    def __init__(self, lib, root):
        self.lib = lib
        self.root = root
        self.name = os.path.basename(root)
        self.parseConfig()
        self.setIcon()

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
        self.dependencies = self.depify(cfg_dict['dependencies'])
        self.oll_core_version = cfg_dict['oll-core']
        self.maintainers = cfg_dict['maintainers']
        self.version = cfg_dict['version']
        self.license = cfg_dict['license']
        self.repository = cfg_dict['repository']


    def depify(self, dependencies):
        pair = re.compile(r"^(.*):\s+(.*)$")
        result = []
        print(self.name)
        print(dependencies)
        for d in dependencies:
            m = pair.search(d)
            if m:
                result.append((m.group(1), m.group(2)))
            else:
                result.append((d, '0.0.0'))
        return result


    def setIcon(self):
        icon = True if 'icon.svg' in os.listdir(self.root) else False
        if icon:
            self.icon = QIcon(os.path.join(self.root, 'icon.svg'))
        else:
            self.icon = icons.get("package")

