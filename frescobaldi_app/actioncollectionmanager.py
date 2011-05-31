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
Manages ActionCollections for a MainWindow (and so, effectively, for the whole
application.)

This makes it possible to edit actions and check whether keyboard shortcuts of
actions conflict with other actions.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtGui import QMessageBox

import actioncollection
import plugin


def manager(mainwindow):
    """Returns the ActionCollectionManager belonging to mainwindow."""
    return ActionCollectionManager.instance(mainwindow)


class ActionCollectionManager(plugin.MainWindowPlugin):
    """Manages ActionCollections for a MainWindow."""
    def __init__(self, mainwindow):
        """Creates the ActionCollectionManager for the given mainwindow."""
        self._actioncollections = []
    
    def addActionCollection(self, collection):
        """Add an actioncollection to our list (used for changing keyboard shortcuts).
        
        Does not keep a reference to it.  If the ActionCollection gets garbage collected,
        it is removed automatically from our list.
        
        """
        ref = weakref.ref(collection)
        if ref not in self._actioncollections:
            self._actioncollections.append(ref)
        
    def removeActionCollection(self, collection):
        """Removes the given ActionCollection from our list."""
        ref = weakref.ref(collection)
        try:
            self._actioncollections.remove(ref)
        except ValueError:
            pass

    def actionCollections(self):
        """Iterate over the ActionCollections in our list."""
        for ref in self._actioncollections[:]: # copy
            collection = ref()
            if collection:
                yield collection
            else:
                self._actioncollections.remove(ref)
        
    def editAction(self, parent, action, default=None, skip=None):
        """Edits the keyboard shortcut for a single action.
        
        Returns True if editing was Ok, False if cancelled.
        parent is the widget to show the dialog above.
        default gives None or a list with QKeySequence objects that are the default shortcut.
        Use skip to give the action to skip (e.g. the action that is about to be changed).
        
        Just uses the dialog in widgets.shortcuteditdialog but implements conflict checking
        (without altering other shortcuts. The implementation of conflict checking in 
        preferences/shortcuts.py also can change other shortcuts in the prefs dialog.)
       
        """
        if skip is None:
            skip = action
            
        from widgets import shortcuteditdialog
        dlg = shortcuteditdialog.ShortcutEditDialog(parent)
        
        while dlg.editAction(action, default):
            # conflict checking
            shortcuts = action.shortcuts()
            if shortcuts:
                conflicts = {}
                for collection in self.actionCollections():
                    for name, a in collection.actions().items():
                        # we use collection.shortcuts(name) instead of a.shortcuts()
                        # because the (real) actions returned by ShortcutCollection.action()
                        # don't have the shortcuts set.
                        if a is not skip and collection.shortcuts(name):
                            for s1 in collection.shortcuts(name):
                                for s2 in action.shortcuts():
                                    if s2.matches(s1) or s1.matches(s2):
                                        # s2 conflicts with a
                                        conflicts.setdefault(a, []).append(s2)
                                        # do shortcuts remain?
                                        if s2 in shortcuts:
                                            shortcuts.remove(s2)
                if conflicts:
                    msg = [_("This shortcut conflicts with the following command:",
                            "This shortcut conflicts with the following commands:", len(conflicts))]
                    msg.append("<br/>".join("{name} ({key})".format(
                        name = actioncollection.removeAccels(a.text()),
                        key=' \u2014 '.join(s.toString() for s in conflicts[a])) for a in conflicts))
                    msg = '<p>{0}</p>'.format('</p><p>'.join(msg))
                    box = QMessageBox(QMessageBox.Warning, _("Shortcut Conflict"), msg,
                            QMessageBox.Ok | QMessageBox.Cancel, parent)
                    box.button(QMessageBox.Ok).setText(_("Edit again"))
                    if box.exec_() == QMessageBox.Ok:
                        action.setShortcuts(shortcuts)
                        continue
                    else:
                        dlg.deleteLater()
                        return False
            dlg.deleteLater()
            return True
        dlg.deleteLater()
        return False


