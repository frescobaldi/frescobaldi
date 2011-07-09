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
import parts._base


class ScorePartsWidget(QSplitter):
    def __init__(self, parent):
        super(ScorePartsWidget, self).__init__(parent)
        
        self.typesLabel = QLabel()
        self.typesView = QTreeView(selectionMode=QTreeView.ExtendedSelection,
                                   selectionBehavior=QTreeView.SelectRows,
                                   headerHidden=True)
        self.scoreLabel = QLabel()
        self.scoreView = ScoreView()
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
        
        # signal connections
        self.addButton.clicked.connect(self.slotAddButtonClicked)
        self.removeButton.clicked.connect(self.slotRemoveButtonClicked)
        self.typesView.doubleClicked.connect(self.slotDoubleClicked)
        self.scoreView.currentItemChanged.connect(self.slotCurrentItemChanged)
        self.upButton.clicked.connect(self.scoreView.moveSelectedChildrenUp)
        self.downButton.clicked.connect(self.scoreView.moveSelectedChildrenDown)
        
    def translateUI(self):
        bold = "<b>{0}</b>".format
        self.typesLabel.setText(bold(_("Available parts:")))
        self.scoreLabel.setText(bold(_("Score:")))
        self.addButton.setText(_("&Add"))
        self.removeButton.setText(_("&Remove"))
        self.upButton.setToolTip(_("Move up"))
        self.downButton.setToolTip(_("Move down"))

    def slotDoubleClicked(self, index):
        self.addParts([index])
        
    def slotAddButtonClicked(self):
        self.addParts(self.typesView.selectedIndexes())

    def addParts(self, indexes):
        """Adds the parts for the given indexes."""
        for index in indexes:
            category = index.internalPointer()
            if category:
                part = category.items[index.row()]
                box = QGroupBox(self.partSettings)
                self.partSettings.addWidget(box)
                item = PartItem(self.scoreView, part, box)
                self.scoreView.addTopLevelItem(item)
    
    def slotCurrentItemChanged(self, item):
        if isinstance(item, PartItem):
            self.partSettings.setCurrentWidget(item.box)
    
    def slotRemoveButtonClicked(self):
        self.scoreView.removeSelectedItems()
        


class ScoreView(QTreeWidget):
    def __init__(self, parent=None):
        super(ScoreView, self).__init__(parent,
            selectionMode=QTreeView.ExtendedSelection,
            selectionBehavior=QTreeView.SelectRows,
            headerHidden=True,
            dragDropMode=QTreeView.InternalMove)
    
    def removeSelectedItems(self, item=None):
        """Removes all selected items from the specified item or the root item."""
        if item is None:
            item = self.invisibleRootItem()
        remove = []
        for i in range(item.childCount()):
            child = item.child(i)
            if child.isSelected():
                remove.append(child)
            else:
                self.removeSelectedItems(child)
        for i in remove:
            i.box.deleteLater()
            item.removeChild(i)
    
    def findSelectedItem(self, item=None):
        """Returns an item that has selected children, if any exists.
        
        The item closest to the specified item or the root item that
        has selected children, is returned.
        
        """
        if item is None:
            item = self.invisibleRootItem()
        for i in range(item.childCount()):
            if item.child(i).isSelected():
                return item
        for i in range(item.childCount()):
            child = item.child(i)
            r = self.findSelectedItem(child)
            if r:
                return r
    
    def moveSelectedChildrenUp(self):
        item = self.findSelectedItem()
        if item:
            for row in range(1, item.childCount()):
                if item.child(row).isSelected():
                    i = item.takeChild(row)
                    item.insertChild(row - 1, i)
                    i.setSelected(True)

    def moveSelectedChildrenDown(self):
        item = self.findSelectedItem()
        if item:
            for row in range(item.childCount() - 2, -1, -1):
                if item.child(row).isSelected():
                    i = item.takeChild(row)
                    item.insertChild(row + 1, i)
                    i.setSelected(True)


    
class PartItem(QTreeWidgetItem):
    def __init__(self, tree, part, box):
        super(PartItem, self).__init__(tree)
        self.part = part()
        self.box = box
        layout = QVBoxLayout()
        box.setLayout(layout)
        self.part.createWidgets(layout)
        app.translateUI(self)
        
        flags = (
            Qt.ItemIsSelectable |
            Qt.ItemIsDragEnabled |
            Qt.ItemIsEnabled
        )
        if isinstance(part, parts._base.Container):
            flags |= Qt.ItemIsDropEnabled
        self.setFlags(flags)
        
    def translateUI(self):
        self.setText(0, self.part.title())
        self.box.setTitle(self.part.title())
        self.part.translateWidgets()
        
