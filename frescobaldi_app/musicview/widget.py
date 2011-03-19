# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
The PDF preview panel widget.
"""

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4
import qpopplerview

import app
import icons
import textformats


class MusicView(QWidget):
    def __init__(self, dockwidget):
        super(MusicView, self).__init__(dockwidget)
        
        self._positions = weakref.WeakKeyDictionary()
        self._currentDocument = lambda: None
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.view = qpopplerview.View(self)
        layout.addWidget(self.view)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        self.view.setViewMode(qpopplerview.FitWidth)
        self.view.viewModeChanged.connect(self.slotViewModeChanged)
        self.slotViewModeChanged(self.view.viewMode())
        
    def sizeHint(self):
        return self.parent().mainwindow().size() / 2
        
    def slotViewModeChanged(self, viewmode):
        ac = self.parent().actionCollection
        ac.music_fit_width.setChecked(viewmode == qpopplerview.FitWidth)
        ac.music_fit_height.setChecked(viewmode == qpopplerview.FitHeight)
        ac.music_fit_both.setChecked(viewmode == qpopplerview.FitBoth)

    def openDocument(self, doc):
        """Opens a documents.Document instance."""
        cur = self._currentDocument()
        if cur:
            self._positions[cur] = self.view.position()
            
        self._currentDocument = weakref.ref(doc)
        self.view.load(doc.document())
        position = self._positions.get(doc, (0, 0, 0))
        self.view.setPosition(position)

    def clear(self):
        """Empties the view."""
        cur = self._currentDocument()
        if cur:
            self._positions[cur] = self.view.position()
        self._currentDocument = lambda: None
        self.view.clear()
        
    def readSettings(self):
        qpopplerview.cache.options().setPaperColor(textformats.formatData('editor').baseColors['paper'])
        self.view.redraw()

