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

from . import model

class Widget(QWidget):
    def __init__(self, panel):
        super(Widget, self).__init__(panel)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        
        self.searchEntry = SearchLineEdit()
        self.treeView = QTreeView()
        self.treeView.setHeaderHidden(True)
        self.infoLine = QLabel()
        self.textView = QTextBrowser()
        
        self.addButton = QToolButton(autoRaise=True, icon=icons.get('list-add'))
        self.editButton = QToolButton(autoRaise=True, icon=icons.get('preferences-system'))
        self.removeButton = QToolButton(autoRaise=True, icon=icons.get('list-remove'))
        self.applyButton = QToolButton(autoRaise=True, icon=icons.get('edit-paste'))
        
        top = QHBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.treeView)
        layout.addWidget(self.infoLine)
        layout.addWidget(self.textView)
        
        top.addWidget(self.searchEntry)
        top.addSpacing(10)
        top.addWidget(self.addButton)
        top.addWidget(self.editButton)
        top.addWidget(self.removeButton)
        top.addSpacing(10)
        top.addWidget(self.applyButton)
        
        # signals
        self.searchEntry.returnPressed.connect(self.slotReturnPressed)
        
        # hide if ESC pressed in lineedit
        a = QAction(self.searchEntry)
        self.searchEntry.addAction(a)
        a.setShortcut(QKeySequence(Qt.Key_Escape))
        a.setShortcutContext(Qt.WidgetShortcut)
        a.triggered.connect(self.slotEscapePressed)
        
        self.treeView.setSelectionBehavior(QTreeView.SelectRows)
        self.treeView.setSelectionMode(QTreeView.ExtendedSelection)
        self.treeView.setRootIsDecorated(False)
        self.treeView.setModel(model.model())
        
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


class SearchLineEdit(widgets.lineedit.LineEdit):
    def __init__(self, *args):
        super(SearchLineEdit, self).__init__(*args)
    
    def event(self, ev):
        if ev.type() == QEvent.KeyPress and any(ev.matches(key) for key in (
            QKeySequence.MoveToNextLine, QKeySequence.SelectNextLine,
            QKeySequence.MoveToPreviousLine, QKeySequence.SelectPreviousLine,
            QKeySequence.MoveToNextPage, QKeySequence.SelectNextPage,
            QKeySequence.MoveToPreviousPage, QKeySequence.SelectPreviousPage)):
            QApplication.sendEvent(self.parent().treeView, ev)
            return True
        return super(SearchLineEdit, self).event(ev)


