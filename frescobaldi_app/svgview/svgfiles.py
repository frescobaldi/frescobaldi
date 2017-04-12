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
Handles SVG files.
"""


import os

from PyQt5.QtCore import Qt, QUrl

import icons
import plugin
import signals
import jobmanager
import resultfiles
import listmodel


class SvgFiles(plugin.DocumentPlugin):
    def __init__(self, document):
        self._files = None
        self.current = 0
        document.loaded.connect(self.invalidate, -100)
        jobmanager.manager(document).finished.connect(self.invalidate, -100)

    def invalidate(self):
        self._files = None

    def update(self):
        files = resultfiles.results(self.document()).files('.svg*')
        self._files = files
        if files and self.current >= len(files):
            self.current = len(files) - 1
        return bool(files)

    def __bool__(self):
        return bool(self._files)

    def model(self):
        """Returns a model for a combobox."""
        if self._files is None:
            self.update()
        m = listmodel.ListModel(self._files,
            display = os.path.basename, icon = icons.file_type)
        m.setRoleFunction(Qt.UserRole, lambda f: f)
        return m

    def url(self, index):
        """Return the filename at index as a QUrl.fromLocalFile()"""
        if self._files is None:
            self.update()
        return QUrl.fromLocalFile(self._files[index])

    def filename(self, index):
        """Return the filename at index."""
        if self._files is None:
            self.update()
        return self._files[index]

