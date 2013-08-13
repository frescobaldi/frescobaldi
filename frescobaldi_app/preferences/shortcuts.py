# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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

from __future__ import unicode_literals

import itertools

from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import (
    QAction, QKeySequence, QMessageBox, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout)

import app
import actioncollectionmanager
import icons
import qutil
import preferences

from widgets.shortcuteditdialog import ShortcutEditDialog
from widgets.schemeselector import SchemeSelector

_lastaction = '' # last selected action name (saved during running but not on exit)


class Shortcuts(preferences.Page):
    def __init__(self, dialog):
        super(Shortcuts, self).__init__(dialog)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.scheme = SchemeSelector(self)
        layout.addWidget(self.scheme)
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
        left = allactions.keys()
        
        def childactions(menu):
            for a in menu.actions():
                if a.menu():
                    for a in childactions(a.menu()):
                        yield a
                elif a in left:
                    yield a
                    left.remove(a)
                
        # present the actions nicely ordered as in the menus
        for a in win.menuBar().actions():
            menuitem = QTreeWidgetItem()
            menu = a.menu()
            text = qutil.removeAccelelator(a.text())
            for a in childactions(menu):
                menuitem.addChild(ShortcutItem(a, *allactions[a]))
            if menuitem.childCount():
                menuitem.setText(0, _("Menu {name}:").format(name=text))
                self.tree.addTopLevelItem(menuitem)
                menuitem.setExpanded(True)
                menuitem.setFlags(Qt.ItemIsEnabled) # disable selection
        
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
            item.setExpanded(True)
            item.setFlags(Qt.ItemIsEnabled) # disable selection
            
        # show other actions that were not in the menus
        item = QTreeWidgetItem([_("Other commands:")])
        for a in left:
            if a.text() and not a.menu():
                item.addChild(ShortcutItem(a, *allactions[a]))
        if item.childCount():
            self.tree.addTopLevelItem(item)
            item.setExpanded(True)
            item.setFlags(Qt.ItemIsEnabled) # disable selection
        
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
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            for j in range(top.childCount()):
                yield top.child(j)
    
    def item(self, collection, name):
        for item in self.items():
            print item.collection.name, item.name
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
    
    def editCurrentItem(self):
        item = self.tree.currentItem()
        if not isinstance(item, ShortcutItem):
            return
        try:
            dlg = self._editdialog
        except AttributeError:
            dlg = self._editdialog = ShortcutEditDialog(self)
        scheme = self.scheme.currentScheme()
        action = item.action(scheme)
        default = item.defaultShortcuts()
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
                # show a question dialog
                msg = [_("This shortcut conflicts with the following command:",
                        "This shortcut conflicts with the following commands:", len(conflicting))]
                msg.append('<br/>'.join(i.text(0) for i in conflicting))
                msg.append(_("Remove the shortcut from that command?",
                             "Remove the shortcut from those commands?", len(conflicting)))
                msg = '<p>{0}</p>'.format('</p><p>'.join(msg))
                res = QMessageBox.warning(self, _("Shortcut Conflict"), msg,
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                if res == QMessageBox.Yes:
                    # remove from conflicting
                    for i in conflicting:
                        l = i.shortcuts(scheme)
                        for s1 in list(l): # copy
                            for s2 in shortcuts:
                                if s1.matches(s2) or s2.matches(s1):
                                    l.remove(s1)
                        i.setShortcuts(l, scheme)
                elif res == QMessageBox.No:
                    # remove from ourselves
                    for i in conflicting:
                        for s1 in list(shortcuts): # copy
                            for s2 in i.shortcuts(scheme):
                                if s1.matches(s2) or s2.matches(s1):
                                    shortcuts.remove(s1)
                else:
                    return # cancelled
            # store the shortcut
            item.setShortcuts(shortcuts, scheme)
            self.changed.emit()

        
class ShortcutItem(QTreeWidgetItem):
    def __init__(self, action, collection, name):
        QTreeWidgetItem.__init__(self)
        self.collection = collection
        self.name = name
        self.setIcon(0, action.icon())
        self.setText(0, qutil.removeAccelelator(action.text()))
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
                    # PyQt4 raises TypeError when an empty list was stored
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
        
        

