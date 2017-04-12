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
Keyboard shortcuts settings page.
"""


import itertools

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout)

import app
import actioncollectionmanager
import icons
import qutil
import preferences

from widgets.shortcuteditdialog import ShortcutEditDialog
from widgets.schemeselector import SchemeSelector
from widgets.lineedit import LineEdit

_lastaction = '' # last selected action name (saved during running but not on exit)


class Shortcuts(preferences.Page):
    def __init__(self, dialog):
        super(Shortcuts, self).__init__(dialog)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.scheme = SchemeSelector(self)
        layout.addWidget(self.scheme)
        self.searchEntry = LineEdit()
        self.searchEntry.setPlaceholderText(_("Search..."))
        layout.addWidget(self.searchEntry)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels([_("Command"), _("Shortcut")])
        self.tree.setRootIsDecorated(False)
        self.tree.setColumnCount(2)
        self.tree.setAllColumnsShowFocus(True)
        self.tree.setAnimated(True)
        layout.addWidget(self.tree)

        self.edit = QPushButton(icons.get("preferences-desktop-keyboard-shortcuts"), '')
        layout.addWidget(self.edit)

        # signals
        self.searchEntry.textChanged.connect(self.updateFilter)
        self.scheme.currentChanged.connect(self.slotSchemeChanged)
        self.scheme.changed.connect(self.changed)
        self.tree.currentItemChanged.connect(self.slotCurrentItemChanged)
        self.tree.itemDoubleClicked.connect(self.editCurrentItem)
        self.edit.clicked.connect(self.editCurrentItem)

        # make a dict of all actions with the actions as key and the names as
        # value, with the collection prepended (for loading/saving)
        win = dialog.parent()
        allactions = {}
        for collection in actioncollectionmanager.manager(win).actionCollections():
            for name, action in collection.actions().items():
                allactions[action] = (collection, name)

        # keep a list of actions not in the menu structure
        left = list(allactions.keys())

        def add_actions(menuitem, actions):
            """Add actions to a QTreeWidgetItem."""
            for a in actions:
                if a.menu():
                    item = build_menu_item(a)
                    if item.childCount():
                        menuitem.addChild(item)
                elif a in left:
                    left.remove(a)
                    menuitem.addChild(ShortcutItem(a, *allactions[a]))
            menuitem.setFlags(Qt.ItemIsEnabled) # disable selection

        def build_menu_item(action):
            """Return a QTreeWidgetItem with children for all the actions in the submenu."""
            menuitem = QTreeWidgetItem()
            text = qutil.removeAccelerator(action.text())
            menuitem.setText(0, _("Menu {name}").format(name=text))
            add_actions(menuitem, action.menu().actions())
            return menuitem

        # present the actions nicely ordered as in the menus
        for a in win.menuBar().actions():
            menuitem = build_menu_item(a)
            if menuitem.childCount():
                self.tree.addTopLevelItem(menuitem)

        # sort leftover actions
        left.sort(key=lambda i: i.text())

        # show actions that are left, grouped by collection
        titlegroups = {}
        for a in left[:]: # copy
            collection, name = allactions[a]
            if collection.title():
                titlegroups.setdefault(collection.title(), []).append(a)
                left.remove(a)
        for title in sorted(titlegroups):
            item = QTreeWidgetItem(["{0}:".format(title)])
            for a in titlegroups[title]:
                item.addChild(ShortcutItem(a, *allactions[a]))
            self.tree.addTopLevelItem(item)
            item.setFlags(Qt.ItemIsEnabled) # disable selection

        # show other actions that were not in the menus
        item = QTreeWidgetItem([_("Other commands:")])
        for a in left:
            if a.text() and not a.menu():
                item.addChild(ShortcutItem(a, *allactions[a]))
        if item.childCount():
            self.tree.addTopLevelItem(item)
            item.setFlags(Qt.ItemIsEnabled) # disable selection

        self.tree.expandAll()

        item = self.tree.topLevelItem(0).child(0)
        if _lastaction:
            # find the previously selected item
            for i in self.items():
                if i.name == _lastaction:
                    item = i
                    break
        self.tree.setCurrentItem(item)
        self.tree.resizeColumnToContents(0)

    def items(self):
        """Yield all the items in the actions tree."""
        def children(item):
            for i in range(item.childCount()):
                c = item.child(i)
                if c.childCount():
                    for c1 in children(c):
                        yield c1
                else:
                    yield c
        for c in children(self.tree.invisibleRootItem()):
            yield c

    def item(self, collection, name):
        for item in self.items():
            if item.collection.name == collection and item.name == name:
                return item

    def saveSettings(self):
        self.scheme.saveSettings("shortcut_scheme", "shortcut_schemes", "shortcuts")
        for item in self.items():
            for scheme in self.scheme.schemes():
                item.save(scheme)
            item.clearSettings()
            item.switchScheme(self.scheme.currentScheme())

    def loadSettings(self):
        self.scheme.loadSettings("shortcut_scheme", "shortcut_schemes")
        # clear the settings in all the items
        for item in self.items():
            item.clearSettings()
            item.switchScheme(self.scheme.currentScheme())

    def slotSchemeChanged(self):
        """Called when the Scheme combobox is changed by the user."""
        for item in self.items():
            item.switchScheme(self.scheme.currentScheme())

    def slotCurrentItemChanged(self, item):
        if isinstance(item, ShortcutItem):
            self.edit.setText(
                _("&Edit Shortcut for \"{name}\"").format(name=item.text(0)))
            self.edit.setEnabled(True)
            global _lastaction
            _lastaction = item.name
        else:
            self.edit.setText(_("(no shortcut)"))
            self.edit.setEnabled(False)

    def import_(self, filename):
        from . import import_export
        import_export.importShortcut(filename, self, self.scheme)

    def export(self, name, filename):
        from . import import_export
        try:
            import_export.exportShortcut(self, self.scheme.currentScheme(), name, filename)
        except (IOError, OSError) as e:
            QMessageBox.critical(self, _("Error"), _(
                "Can't write to destination:\n\n{url}\n\n{error}").format(
                url=filename, error=e.strerror))

    def findShortcutConflict(self, shortcut):
        """Find the possible shortcut conflict and return the conflict name."""
        if shortcut:
            item = self.tree.currentItem()
            if not isinstance(item, ShortcutItem):
                return None
            scheme = self.scheme.currentScheme()
            for i in self.items():
                a = i.action(scheme)
                if i != item and a.shortcuts():
                    for s1 in a.shortcuts():
                        if s1.matches(shortcut) or shortcut.matches(s1):
                            return qutil.removeAccelerator(a.text())
        return None

    def editCurrentItem(self):
        item = self.tree.currentItem()
        if not isinstance(item, ShortcutItem):
            return

        dlg = ShortcutEditDialog(self, self.findShortcutConflict)
        scheme = self.scheme.currentScheme()
        action = item.action(scheme)
        default = item.defaultShortcuts() or None
        if dlg.editAction(action, default):
            shortcuts = action.shortcuts()
            # check for conflicts
            conflicting = []
            for i in self.items():
                if i is not item:
                    for s1, s2 in itertools.product(i.shortcuts(scheme), shortcuts):
                        if s1.matches(s2) or s2.matches(s1):
                            conflicting.append(i)
            if conflicting:
                for i in conflicting:
                    l = i.shortcuts(scheme)
                    for s1 in list(l): # copy
                        for s2 in shortcuts:
                            if s1.matches(s2) or s2.matches(s1):
                                l.remove(s1)
                    i.setShortcuts(l, scheme)

            # store the shortcut
            item.setShortcuts(shortcuts, scheme)
            self.changed.emit()

    def updateFilter(self):
        """Called when the search text changes."""
        search = self.searchEntry.text()
        scheme = self.scheme.currentScheme()
        def hidechildren(item):
            hideparent = True
            for n in range(item.childCount()):
                c = item.child(n)
                if c.childCount():
                    # submenu item
                    if hidechildren(c):
                        c.setHidden(True)
                    else:
                        c.setHidden(False)
                        c.setExpanded(True)
                        hideparent = False
                elif isinstance(c, ShortcutItem):
                    # shortcut item, should be the case
                    if c.matches(scheme, search):
                        c.setHidden(False)
                        hideparent = False
                    else:
                        c.setHidden(True)
            return hideparent
        hidechildren(self.tree.invisibleRootItem())


class ShortcutItem(QTreeWidgetItem):
    def __init__(self, action, collection, name):
        QTreeWidgetItem.__init__(self)
        self.collection = collection
        self.name = name
        self.setIcon(0, action.icon())
        self.setText(0, qutil.removeAccelerator(action.text()))
        self._shortcuts = {}

    def clearSettings(self):
        self._shortcuts.clear()

    def action(self, scheme):
        """Returns a new QAction that represents our item.

        The action contains the text, icon and current shortcut.

        """
        action = QAction(self.icon(0), self.text(0).replace('&', '&&'), None)
        action.setShortcuts(self._shortcuts[scheme][0])
        return action

    def shortcuts(self, scheme):
        """Returns the list of shortcuts currently set for scheme."""
        return list(self._shortcuts[scheme][0])

    def isDefault(self, scheme):
        return self._shortcuts[scheme][1]

    def setShortcuts(self, shortcuts, scheme):
        default = shortcuts == self.defaultShortcuts()
        self._shortcuts[scheme] = (shortcuts, default)
        self.display(scheme)

    def defaultShortcuts(self):
        """Returns a (possibly empty) list of QKeySequence objects.

        The list represents the default shortcut for this item, if any.

        """
        return self.collection.defaults().get(self.name, [])

    def switchScheme(self, scheme):
        if scheme not in self._shortcuts:
            s = QSettings()
            key = "shortcuts/{0}/{1}/{2}".format(scheme, self.collection.name, self.name)
            if s.contains(key):
                try:
                    shortcuts = s.value(key, [], QKeySequence)
                except TypeError:
                    # PyQt5 raises TypeError when an empty list was stored
                    shortcuts = []
                self._shortcuts[scheme] = (shortcuts, False)
            else:
                # default
                self._shortcuts[scheme] = (self.defaultShortcuts(), True)
        self.display(scheme)

    def save(self, scheme):
        try:
            shortcuts, default = self._shortcuts[scheme]
        except KeyError:
            return
        s =QSettings()
        key = "shortcuts/{0}/{1}/{2}".format(scheme, self.collection.name, self.name)
        if default:
            s.remove(key)
        else:
            s.setValue(key, shortcuts)

    def display(self, scheme):
        text = ''
        shortcuts, default = self._shortcuts[scheme]
        if shortcuts:
            text = shortcuts[0].toString(QKeySequence.NativeText)
            if len(shortcuts) > 1:
                text += "..."
            if default:
                text += "  " + _("(default)")
        self.setText(1, text)

    def matches(self, scheme, text):
        """Return True if the text matches our description or shortcuts.

        Shortcuts are checked in the specified scheme.
        The match is case insensitive.

        """
        text = text.lower()
        if text in self.text(0).lower():
            return True
        for shortcut in self.shortcuts(scheme):
            if text in shortcut.toString(QKeySequence.NativeText).lower():
                return True
        return False


