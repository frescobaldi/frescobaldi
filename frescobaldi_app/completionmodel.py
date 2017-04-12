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
import weakref

from PyQt5.QtCore import QSettings, QStringListModel, QTimer
from PyQt5.QtWidgets import QCompleter

import qsettings # for safely retrieving list of strings


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


def complete(lineedit, key):
    """A convenience function that installs a completer on the QLineEdit.

    The key is the QSettings key used to store the completions persistently.
    By default, the function tries to add the text in the line edit to
    the stored completions when the window() of the lineedit is a Dialog
    and its accepted signal is fired.

    Returned is a callable a signal can be connected to, that stores the text
    in the line edit in the completions. (You don't have to use that if your
    widget is in a QDialog that has an accepted() signal.)

    """
    m = model(key)
    c = QCompleter(m, lineedit)
    lineedit.setCompleter(c)
    def store(completer = weakref.ref(c)):
        """Stores the contents of the line edit in the completer's model.

        Does not keep a reference to any object.

        """
        c = completer()
        if c:
            model = c.model()
            lineedit = c.parent()
            if model and lineedit:
                text = lineedit.text().strip()
                if text:
                    model.addString(text)
    def connect():
        """Try to connect the store() function to the accepted() signal of the parent QDialog.

        Return True if that succeeds, else False.

        """
        dlg = lineedit.window()
        try:
            dlg.accepted.connect(store)
        except AttributeError:
            return False
        return True
    connect() or QTimer.singleShot(0, connect)
    return store


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
        strings = qsettings.get_string_list(QSettings(), self.key)
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


