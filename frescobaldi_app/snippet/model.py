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
The model containing the snippets data.
"""



import bisect

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt5.QtGui import QKeySequence

import app
import actioncollection

from . import snippets


def model():
    """Returns the global model containing snippets."""
    m = SnippetModel(app.qApp)
    global model
    model = lambda: m
    return m


class SnippetModel(QAbstractItemModel):
    """Presents the snippets as a Qt Model."""
    def __init__(self, parent = None):
        super(SnippetModel, self).__init__(parent)
        self._names = []
        self.load()
        app.settingsChanged.connect(self.slotSettingsChanged)
        app.languageChanged.connect(self.slotLanguageChanged)

    # methods needed to be a well-behaved model
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return _("Name")
            elif section == 1:
                return _("Description")
            else:
                return _("Shortcut")

    def index(self, row, column, parent=None):
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()

    def columnCount(self, parent=QModelIndex()):
        return 3 if not parent.isValid() else 0

    def rowCount(self, parent=QModelIndex()):
        return len(self._names) if not parent.isValid() else 0

    def data(self, index, role=Qt.DisplayRole):
        name = self.name(index)
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return snippets.get(name).variables.get('name')
            elif index.column() == 1:
                return snippets.title(name)
            else:
                return shortcut(name)
        elif role == Qt.DecorationRole and index.column() == 1:
            return snippets.icon(name)

    # slots
    def slotSettingsChanged(self):
        """Called when settings change, e.g. when keyboard shortcuts are altered."""
        self.load()

    def slotLanguageChanged(self):
        """Called when the user changes the language."""
        self.headerDataChanged.emit(Qt.Horizontal, 0, 2)

    def load(self):
        self.beginResetModel()
        self._names = sorted(snippets.names(), key=snippets.title)
        self.endResetModel()

    # interface for getting/altering snippets
    def names(self):
        """Returns the internal list of snippet names in title order. Do not alter!"""
        return self._names

    def name(self, index):
        """The internal snippet id for the given QModelIndex."""
        return self._names[index.row()]

    def removeRows(self, row, count, parent=QModelIndex()):
        end = row + count
        self.beginRemoveRows(parent, row, end)
        try:
            for name in self._names[row:end]:
                snippets.delete(name)
            del self._names[row:end]
        finally:
            self.endRemoveRows()
            return True

    def saveSnippet(self, name, text, title):
        """Store a snippet.

        If name is None or does not exist in names(), a new snippet is created.
        Returns the QModelIndex the snippet was stored at.

        Title may be None.

        """
        # first, get the old titles list
        titles = list(snippets.title(n) for n in self._names)

        oldrow = None
        if name is None:
            name = snippets.name(self._names)
        else:
            try:
                oldrow = self._names.index(name)
            except ValueError:
                pass
        snippets.save(name, text, title)
        # sort the new snippet in
        # if oldrow is not None, it is the row to be removed.
        title = snippets.title(name)
        i = bisect.bisect_right(titles, title)

        if oldrow is None:
            # just insert new snippet
            self.beginInsertRows(QModelIndex(), i, i )
            self._names.insert(i, name)
            self.endInsertRows()
            return self.createIndex(i, 0)
        elif i in (oldrow, oldrow+1):
            # just replace
            self._names[oldrow] = name
            self.dataChanged.emit(self.createIndex(oldrow, 0), self.createIndex(oldrow, 2))
            return self.createIndex(oldrow, 0)
        else:
            # move the old row to the new place
            if self.beginMoveRows(QModelIndex(), oldrow, oldrow, QModelIndex(), i):
                del self._names[oldrow]
                if i > oldrow:
                    i -= 1
                self._names.insert(i, name)
                self.endMoveRows()
                self.dataChanged.emit(self.createIndex(i, 0), self.createIndex(i, 2))
                return self.createIndex(i, 0)
            raise RuntimeError("wrong row move offset")


def shortcut(name):
    """Returns a shortcut text for the named snippets, if any, else None."""
    s = shortcuts(name)
    if s:
        text = s[0].toString(QKeySequence.NativeText)
        if len(s) > 1:
            text += "..."
        return text


def shortcuts(name):
    """Returns a (maybe empty) list of QKeySequences for the named snippet."""
    ac = collection()
    return ac and ac.shortcuts(name) or []


def collection():
    """Returns an instance of the 'snippets' ShortcutCollection, if existing."""
    try:
        # HACK alert :-) access an instance of the ShortcutCollection named 'snippets'
        ref = actioncollection.ShortcutCollection.others['snippets'][0]
    except (KeyError, IndexError):
        return
    return ref()


