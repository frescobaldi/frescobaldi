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
Simple readonly subclass of QAbstractListModel around a Python sequence.

Functions are used to present the data from an item for a role.
There are some predefined functions to use in this module.
"""

from PyQt5.QtCore import QAbstractListModel, Qt


def display(item):
    """Displays an item unchanged."""
    return item

def translate(item):
    """Calls an item (normally returning a translation of the item)."""
    return item()

def display_index(index):
    """Returns a function that displays the given index of an item."""
    return lambda item: item[index]

def translate_index(index):
    """Returns a function that translates the given index of an item."""
    return lambda item: item[index]()


class ListModel(QAbstractListModel):
    """A simple QAbstractListModel around a Python list."""
    def __init__(self, data, parent=None, display=display, edit=None, tooltip=None, icon=None):
        """Initializes the list.

        parent may be a parent QObject.
        display, tooltip and icon may be functions that extract the data from an item
        for the respective role (DisplayRole, ToolTipRole or DecorationRole).

        The original data can be found in the _data attribute.

        """
        super(ListModel, self).__init__(parent)
        self._data = data
        self._roles = {}
        if edit is None:
            edit = display
        if display:
            self._roles[Qt.DisplayRole] = display
        if edit:
            self._roles[Qt.EditRole] = edit
        if tooltip:
            self._roles[Qt.ToolTipRole] = tooltip
        if icon:
            self._roles[Qt.DecorationRole] = icon

    def setRoleFunction(self, role, function):
        """Sets a function that returns a value for a Qt.ItemDataRole.

        The function accepts an item in the data list given on construction
        as argument. If function is None, deletes a previously set function.

        """
        if function:
            self._roles[role] = function
        elif role in self._roles:
            del self._roles[role]

    def rowCount(self, parent):
        return 0 if parent.isValid() else len(self._data)

    def data(self, index, role):
        try:
            data = self._data[index.row()]
        except IndexError:
            return
        try:
            f = self._roles[role]
        except KeyError:
            return
        return f(data)

    def update(self):
        """Emits the dataChanged signal for all entries.

        This can e.g. be used to request that translated strings are redisplayed.

        """
        self.dataChanged.emit(
            self.createIndex(0, 0),
            self.createIndex(len(self._data) - 1, 0))


