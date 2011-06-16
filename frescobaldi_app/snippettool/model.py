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


_model = None

def model():
    """Returns the global model containing snippets."""
    global _model
    if _model is None:
        _model = Model(app.qApp)
    return _model


class Model(QAbstractItemModel):
    def __init__(self, parent = None):
        super(Model, self).__init__(parent)
        ### TEMP!
        self._tempstrings = [
            'some string',
            'another string',
            'test value',
            'more tests',
            'yet another test',
            'final test string',
            ]
    
    def index(self, row, column, parent=None):
        return self.createIndex(row, column)
    
    def parent(self, index):
        return QModelIndex()
    
    def columnCount(self, parent):
        return 2
    
    def rowCount(self, parent):
        return len(self._tempstrings)
    
    def data(self, index, role=Qt.DisplayRole):
        ## TEMP!!!
        if role == Qt.DisplayRole:
            if index.column() == 1:
                if index.row() == 3:
                    return "Ctrl+K"
            else:
                return self._tempstrings[index.row()]


                    