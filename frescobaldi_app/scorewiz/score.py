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
The Parts widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons

from . import parts


class ScorePartsWidget(QSplitter):
    def __init__(self, parent):
        super(ScorePartsWidget, self).__init__(parent)
        
        self.typesLabel = QLabel()
        self.typesView = QTreeView()
        self.scoreLabel = QLabel()
        self.scoreView = QTreeView()
        self.addButton = QPushButton(icon = icons.get("list-add"))
        self.removeButton = QPushButton(icon = icons.get("list-remove"))
        self.upButton = QToolButton()
        self.downButton = QToolButton()
        self.partSettings = QStackedWidget()
        
        w = QWidget()
        self.addWidget(w)
        layout = QVBoxLayout(spacing=0)
        w.setLayout(layout)
        
        layout.addWidget(self.typesLabel)
        layout.addWidget(self.typesView)
        layout.addWidget(self.addButton)
        
        w = QWidget()
        self.addWidget(w)
        layout = QVBoxLayout(spacing=0)
        w.setLayout(layout)
        
        layout.addWidget(self.scoreLabel)
        layout.addWidget(self.scoreView)
        
        box = QHBoxLayout(spacing=0)
        layout.addLayout(box)
        
        box.addWidget(self.removeButton)
        box.addWidget(self.upButton)
        box.addWidget(self.downButton)
        
        self.addWidget(self.partSettings)

        self.typesView.setModel(parts.model())
        app.translateUI(self)
        
    def translateUI(self):
        bold = "<b>{0}</b>".format
        self.typesLabel.setText(bold(_("Available parts:")))
        self.scoreLabel.setText(bold(_("Score:")))
        self.addButton.setText(_("&Add"))
        self.removeButton.setText(_("&Remove"))
        self.upButton.setToolTip(_("Move up"))
        self.downButton.setToolTip(_("Move down"))


        

