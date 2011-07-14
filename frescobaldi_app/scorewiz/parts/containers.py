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
Container part types.
"""

import __builtin__

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from scorewiz import scoreproperties

from . import _base
from . import register

class StaffGroup(_base.Container):
    @staticmethod
    def title(_=__builtin__._):
        return _("Staff Group")

    def accepts(self):
        return (StaffGroup, _base.Part)


class Score(_base.Container, scoreproperties.ScoreProperties):
    @staticmethod
    def title(_=__builtin__._):
        return _("Score")

    def createWidgets(self, layout):
        self.pieceLabel = QLabel()
        self.piece = QLineEdit()
        self.pieceLabel.setBuddy(self.piece)
        self.opusLabel = QLabel()
        self.opus = QLineEdit()
        self.opusLabel.setBuddy(self.opus)
        self.scoreProps = QGroupBox(checkable=True, checked=False)
        scoreproperties.ScoreProperties.createWidgets(self)
        
        grid = QGridLayout()
        grid.addWidget(self.pieceLabel, 0 ,0)
        grid.addWidget(self.piece, 0, 1)
        grid.addWidget(self.opusLabel, 1, 0)
        grid.addWidget(self.opus, 1, 1)
        layout.addLayout(grid)
        layout.addWidget(self.scoreProps)
        layout = QVBoxLayout()
        self.scoreProps.setLayout(layout)
        scoreproperties.ScoreProperties.layoutWidgets(self, layout)
        
    def translateWidgets(self):
        self.pieceLabel.setText(_("Piece:"))
        self.opusLabel.setText(_("Opus:"))
        self.scoreProps.setTitle(_("Properties"))
        scoreproperties.ScoreProperties.translateWidgets(self)
        
    def accepts(self):
        return (StaffGroup, _base.Part)


class BookPart(_base.Container):
    @staticmethod
    def title(_=__builtin__._):
        return _("Book Part")

    def accepts(self):
        return (Score, StaffGroup, _base.Part)


class Book(_base.Container):
    @staticmethod
    def title(_=__builtin__._):
        return _("Book")

    def accepts(self):
        return (BookPart, Score, StaffGroup, _base.Part)



register(
    lambda: _("Containers"),
    [
        StaffGroup,
        Score,
        BookPart,
        Book,
    ])
