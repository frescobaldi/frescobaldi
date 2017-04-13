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
The Parts widget.
"""


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QStackedWidget,
    QToolButton, QTreeView, QVBoxLayout, QWidget)

import app
import icons
import widgets.treewidget

from . import parts


class ScorePartsWidget(QSplitter):
    def __init__(self, parent):
        super(ScorePartsWidget, self).__init__(parent)

        self.typesLabel = QLabel()
        self.typesView = QTreeView(
            selectionMode=QTreeView.ExtendedSelection,
            selectionBehavior=QTreeView.SelectRows,
            animated=True,
            headerHidden=True)
        self.scoreLabel = QLabel()
        self.scoreView = widgets.treewidget.TreeWidget(
            selectionMode=QTreeView.ExtendedSelection,
            selectionBehavior=QTreeView.SelectRows,
            headerHidden=True,
            animated=True,
            dragDropMode=QTreeView.InternalMove)
        self.addButton = QPushButton(icon = icons.get("list-add"))
        self.removeButton = QPushButton(icon = icons.get("list-remove"))
        self.upButton = QToolButton(icon = icons.get("go-up"))
        self.downButton = QToolButton(icon = icons.get("go-down"))
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
        # add to current if that is a container type
        currentItem = self.scoreView.currentItem()
        for index in indexes:
            category = index.internalPointer()
            if category:
                part = category.items[index.row()]
                box = QGroupBox(self.partSettings)
                self.partSettings.addWidget(box)
                # determine the parent: current or root
                if currentItem and issubclass(part, currentItem.part.accepts()):
                    parent = currentItem
                    parent.setExpanded(True)
                else:
                    parent = self.scoreView
                item = PartItem(parent, part, box)

    def slotCurrentItemChanged(self, item):
        if isinstance(item, PartItem):
            self.partSettings.setCurrentWidget(item.box)

    def slotRemoveButtonClicked(self):
        self.scoreView.removeSelectedItems()

    def clear(self):
        """Called when the user clicks the clear button on this page."""
        self.scoreView.clear()

    def rootPartItem(self):
        """Returns the invisibleRootItem(), representing the tree of parts in the score view."""
        return self.scoreView.invisibleRootItem()


class PartItem(widgets.treewidget.TreeWidgetItem):
    """An item in the score tree widget."""
    def __init__(self, tree, part, box):
        """Initializes the item.

        tree: is the score tree widget,
        part: is the Part instance that creates the widgets
        box: the QGroupBox that is created for this item in the stacked widget.

        """
        super(PartItem, self).__init__(tree)
        self.part = part()
        self.box = box
        layout = QVBoxLayout()
        box.setLayout(layout)
        self.part.createWidgets(layout)
        layout.addStretch(1)
        app.translateUI(self)

        flags = (
            Qt.ItemIsSelectable |
            Qt.ItemIsDragEnabled |
            Qt.ItemIsEnabled
        )
        if issubclass(part, parts._base.Container):
            flags |= Qt.ItemIsDropEnabled
        self.setFlags(flags)

    def translateUI(self):
        self.setText(0, self.part.title())
        self.box.setTitle(self.part.title())
        self.part.translateWidgets()

    def cleanup(self):
        self.box.deleteLater()


