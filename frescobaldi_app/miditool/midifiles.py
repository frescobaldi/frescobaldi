# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Handles MIDI files.
"""


import os

from PyQt5.QtCore import Qt

import icons
import plugin
import signals
import jobmanager
import resultfiles
import listmodel
import midifile.song


class MidiFiles(plugin.DocumentPlugin):
    def __init__(self, document):
        self._files = None
        self.current = 0
        document.loaded.connect(self.invalidate, -100)
        jobmanager.manager(document).finished.connect(self.invalidate, -100)

    def invalidate(self):
        self._files = None

    def update(self):
        files = resultfiles.results(self.document()).files('.mid*')
        self._files = files
        self._songs = [None] * len(files)
        if files and self.current >= len(files):
            self.current = len(files) - 1
        return bool(files)

    def __bool__(self):
        return bool(self._files)

    def song(self, index):
        if self._files is None:
            self.update()
        song = self._songs[index]
        if not song:
            song = self._songs[index] = midifile.song.load(self._files[index])
        return song

    def model(self):
        """Returns a model for a combobox."""
        if self._files is None:
            self.update()
        m = listmodel.ListModel(self._files,
            display = os.path.basename, icon = icons.file_type)
        m.setRoleFunction(Qt.UserRole, lambda f: f)
        return m


