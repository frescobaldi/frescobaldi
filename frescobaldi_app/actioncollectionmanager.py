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
Manages ActionCollections for a MainWindow (and so, effectively, for the whole
application.)

This makes it possible to edit actions and check whether keyboard shortcuts of
actions conflict with other actions.
"""


import weakref

import actioncollection
import plugin
import qutil


def manager(mainwindow):
    """Returns the ActionCollectionManager belonging to mainwindow."""
    return ActionCollectionManager.instance(mainwindow)

def action(collection_name, action_name):
    """Return a QAction from the application.

    May return None, if the named collection or action does not exist.

    """
    for mgr in ActionCollectionManager.instances():
        return mgr.action(collection_name, action_name)


class ActionCollectionManager(plugin.MainWindowPlugin):
    """Manages ActionCollections for a MainWindow."""
    def __init__(self, mainwindow):
        """Creates the ActionCollectionManager for the given mainwindow."""
        self._actioncollections = weakref.WeakValueDictionary()

    def addActionCollection(self, collection):
        """Add an actioncollection to our list (used for changing keyboard shortcuts).

        Does not keep a reference to it.  If the ActionCollection gets garbage collected,
        it is removed automatically from our list.

        """
        if collection.name not in self._actioncollections:
            self._actioncollections[collection.name] = collection

    def removeActionCollection(self, collection):
        """Removes the given ActionCollection from our list."""
        if collection.name in self._actioncollections:
            del self._actioncollections[collection.name]

    def actionCollections(self):
        """Iterate over the ActionCollections in our list."""
        return self._actioncollections.values()

    def action(self, collection_name, action_name):
        """Returns the named action from the named collection."""
        collection = self._actioncollections.get(collection_name)
        if collection:
            if isinstance(collection, actioncollection.ShortcutCollection):
                return collection.realAction(action_name)
            return getattr(collection, action_name, None)

    def iterShortcuts(self, skip=None):
        """Iter all shortcuts of all collections."""
        for collection in self.actionCollections():
            for name, a in collection.actions().items():
                if (collection, name) != skip:
                    for shortcut in collection.shortcuts(name):
                        yield shortcut, collection, name, a

    def findShortcutConflict(self, shortcut, skip):
        """Find the possible shortcut conflict and return the conflict name.

        skip must be a tuple (collection, name).
        it's the action to skip (the action that is about to be changed).

        """
        if shortcut:
            for data in self.iterShortcuts(skip):
                s1 = data[0]
                if s1.matches(shortcut) or shortcut.matches(s1):
                    return qutil.removeAccelerator(data[-1].text())
        return None

    def removeShortcuts(self, shortcuts):
        """Find and remove shorcuts of the given list."""
        for data in self.iterShortcuts():
            s1, collection, name = data[:3]
            for s2 in shortcuts:
                if s2.matches(s1) or s1.matches(s2):
                    collShortcuts = collection.shortcuts(name)
                    collShortcuts.remove(s1)
                    collection.setShortcuts(name, collShortcuts)

