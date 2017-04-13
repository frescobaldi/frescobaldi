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
A TreeWidget with some useful methods to manipulate items.
"""


from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem


class TreeWidget(QTreeWidget):
    """A QTreeWidget with some item-manipulation methods.

    We use a widget instead of a view with a standard model because
    this lets us really have control over the items. With a standard
    model, items are recreated e.g. when dragging and this loses the
    python subclassed instances with their own parameters.

    Calls the cleanup() method on QTreeWidgetItems as they are removed,
    but does not error out if the QTreeWidgetItem does not have a cleanup()
    method.

    """
    def __init__(self, parent=None, **kws):
        super(TreeWidget, self).__init__(parent, **kws)

    def items(self, parent=None):
        """Yields all items from parent or the invisibleRootItem."""
        if parent is None:
            parent = self.invisibleRootItem()
        for i in range(parent.childCount()):
            c = parent.child(i)
            for i in self.items(c):
                yield i
            yield c

    def clear(self):
        """Removes all items, calling their cleanup() method (if available) first."""
        for item in self.items():
            self._cleanup(item)
        super(TreeWidget, self).clear()

    def removeSelectedItems(self, item=None):
        """Removes all selected items from the specified item or the root item."""
        if item is None:
            item = self.invisibleRootItem()
        itemsToRemove = []
        for i in range(item.childCount()):
            child = item.child(i)
            if child.isSelected():
                itemsToRemove.append(child)
            else:
                self.removeSelectedItems(child)
        for child in itemsToRemove:
            for descendant in self.items(child):
                self._cleanup(descendant)
            item.removeChild(child)
            self._cleanup(child)

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

    @staticmethod
    def _cleanup(item):
        """Calls item.cleanup() if the QTreeWidgetItem has that method."""
        if hasattr(item, 'cleanup'):
            item.cleanup()


class TreeWidgetItem(QTreeWidgetItem):
    def cleanup(self):
        """May be implemented to perform cleanup when an item is removed."""


