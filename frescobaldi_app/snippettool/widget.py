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
The snippets widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons
import widgets.lineedit


class Widget(QWidget):
    def __init__(self, panel):
        super(Widget, self).__init__(panel)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.searchEntry = widgets.lineedit.LineEdit()
        self.listView = QListView()
        self.infoLine = QLabel()
        self.textView = QTextBrowser()
        
        self.addButton = QToolButton(autoRaise=True, icon=icons.get('list-add'))
        self.editButton = QToolButton(autoRaise=True, icon=icons.get('preferences-system'))
        self.removeButton = QToolButton(autoRaise=True, icon=icons.get('list-remove'))
        self.applyButton = QToolButton(autoRaise=True, icon=icons.get('edit-paste'))
        
        layout.addWidget(self.listView)
        layout.addWidget(self.infoLine)
        layout.addWidget(self.textView)
        
        w = QWidget(self.listView)
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignTop)
        
        self.listView.setLayout(layout)
        layout.addWidget(self.searchEntry)
        layout.addSpacing(10)
        layout.addWidget(self.addButton)
        layout.addWidget(self.editButton)
        layout.addWidget(self.removeButton)
        layout.addSpacing(10)
        layout.addWidget(self.applyButton)
        
        self.listView.setViewportMargins(0, layout.sizeHint().height(), 0, 0)
        
        # signals
        self.searchEntry.returnPressed.connect(self.slotReturnPressed)
        
        # hide if ESC pressed in lineedit
        a = QAction(self.searchEntry)
        self.searchEntry.addAction(a)
        a.setShortcut(QKeySequence(Qt.Key_Escape))
        a.setShortcutContext(Qt.WidgetShortcut)
        a.triggered.connect(self.slotEscapePressed)
        
        self.setInfoText('')
        app.translateUI(self)

    def translateUI(self):
        try:
            self.searchEntry.setPlaceHolderText(_("Search..."))
        except AttributeError:
            pass # not in Qt 4.6
    
    def sizeHint(self):
        return self.parent().mainwindow().size() / 4
        
    def setInfoText(self, text):
        if text:
            self.infoLine.setText(text)
        self.infoLine.setVisible(bool(text))
        
    def slotReturnPressed(self):
        """Called when the user presses Return in the search entry. Applies current template."""
        #TODO: apply current template/snippet
        self.parent().hide() # TODO: make configurable
        self.parent().mainwindow().currentView().setFocus()

    def slotEscapePressed(self):
        """Called when the user presses ESC in the search entry. Hides the panel."""
        self.parent().hide() # TODO: make configurable
        self.parent().mainwindow().currentView().setFocus()

