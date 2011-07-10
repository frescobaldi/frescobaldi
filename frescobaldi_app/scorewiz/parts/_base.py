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
Base types for parts.
"""

import __builtin__
import collections

from PyQt4.QtCore import *
from PyQt4.QtGui import *


Category = collections.namedtuple("Category", "title items icon")



class Part(object):
    """Base class for Parts."""
    @staticmethod
    def title(_=__builtin__._):
        """Should return a title.
        
        If a translator is given, it is used instead of the builtin.
        
        """
    
    @staticmethod
    def short(_=__builtin__._):
        """Should return an abbreviated title.
        
        If a translator is given, it is used instead of the builtin.
        
        """

    def createWidgets(self, layout):
        """Should create widgets to adjust settings."""
        self.noSettingsLabel = QLabel()
        layout.addWidget(self.noSettingsLabel)
        
    def translateWidgets(self):
        """Should set the text in the widgets when the language changes."""
        self.noSettingsLabel.setText('({0})'.format(_("No settings available.")))


class Container(Part):
    """Base class for "part" types that can contain others."""



# Mixin-base classes with basic behaviour
class ChordNames(object):
    def createWidgets(self, layout):
        self.chordStyleLabel = QLabel()
        self.chordStyle = QComboBox()
        self.chordStyleLabel.setBuddy(self.chordStyle)
        self.chordStyle.setModel(ChordNamesModel(self.chordStyle))
        self.guitarFrets = QCheckBox()
        
        box = QHBoxLayout()
        box.addWidget(self.chordStyleLabel)
        box.addWidget(self.chordStyle)
        layout.addLayout(box)
        layout.addWidget(self.guitarFrets)
        
    def translateWidgets(self):
        self.chordStyleLabel.setText(_("Chord style:"))
        self.guitarFrets.setText(_("Guitar fret diagrams"))
        self.guitarFrets.setToolTip(_(
            "Show predefined guitar fret diagrams below the chord names "
            "(LilyPond 2.12 and above)."))
        self.chordStyle.update()


class ChordNamesModel(QAbstractListModel):
    _data = (
        lambda: _("Default"),
        lambda: _("German"),
        lambda: _("Semi-German"),
        lambda: _("Italian"),
        lambda: _("French"),
    )
    
    def rowCount(self, parent):
        return len(self._data)
        
    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()]()

