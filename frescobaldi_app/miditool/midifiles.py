# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QFileInfo, Qt
from PyQt4.QtGui import QFileIconProvider

import app
import plugin
import signals
import resultfiles
import listmodel
import midifile.song


updated = signals.Signal() # Document; emitted if there are new MIDI files.

def _update(document):
    """Checks if MIDI files were updated for the document."""
    if MidiFiles.instance(document).update():
        updated(document)

app.jobFinished.connect(_update)
app.documentLoaded.connect(_update)


class MidiFiles(plugin.DocumentPlugin):
    def __init__(self, document):
        self._files = None
        self.current = 0
    
    def update(self):
        files = resultfiles.results(self.document()).files('.mid*')
        self._files = files
        self._songs = [None] * len(files)
        if files and self.current >= len(files):
            self.current = len(files) - 1
        return bool(files)
    
    def __nonzero__(self):
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
            display = os.path.basename,
            icon = lambda f: QFileIconProvider().icon(QFileInfo(f)))
        m.setRoleFunction(Qt.UserRole, lambda f: f)
        return m


