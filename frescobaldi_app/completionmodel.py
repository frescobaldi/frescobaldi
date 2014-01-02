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
A simple persistent completion model (e.g. for QLineEdits).
"""

import atexit

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QStringListModel

_models = {}


def model(key):
    """Returns the model for the given settings key.
    
    A Model is instantiated if necessary.
    The model remains alive until the application exits, at which
    moment the data is saved.
    
    """
    try:
        return _models[key]
    except KeyError:
        m = _models[key] = Model(key)
        atexit.register(m.save)
        return m


class Model(QStringListModel):
    """A simple model providing a list of strings for a QCompleter.
    
    Instantiate the model with a QSettings key, e.g. 'somegroup/names'.
    Use the addString() method to add a string.
    
    """
    def __init__(self, key):
        super(Model, self).__init__()
        self.key = key
        self._changed = False
        self.load()
        
    def load(self):
        try:
            strings = QSettings().value(self.key, [], type(""))
        except TypeError:
            strings = []
        self.setStringList(sorted(strings))
        self._changed = False
    
    def save(self):
        if self._changed:
            QSettings().setValue(self.key, self.stringList())
            self._changed = False

    def addString(self, text):
        strings = self.stringList()
        if text not in strings:
            strings.append(text)
            strings.sort()
            self.setStringList(strings)
            self._changed = True


