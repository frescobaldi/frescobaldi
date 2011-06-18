# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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


from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
        if role == Qt.DisplayRole:
            name = self.name(index)
            if index.column() == 0:
                return snippets.get(name)[1].get('name')
            elif index.column() == 1:
                return snippets.title(name)
            else:
                return shortcut(name)
    
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
        
    # slots
    def slotSettingsChanged(self):
        """Called when settings change, e.g. when keyboard shortcuts are altered."""
        self.load()
        
    def slotLanguageChanged(self):
        """Called when the user changes the language."""
        self.headerDataChanged.emit(Qt.Horizontal, 0, 1)
        
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



def shortcut(name):
    """Returns a shortcut text for the named snippets, if any, else None."""
    try:
        # HACK alert :-) access an instance of the ShortcutCollection named 'snippets'
        ref = actioncollection.ShortcutCollection.others['snippets'][0]
    except (KeyError, IndexError):
        return
    collection = ref()
    if collection:
        shortcuts = collection.shortcuts(name)
        if shortcuts:
            text = shortcuts[0].toString()
            if len(shortcuts) > 1:
                text += "..."
            return text


