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
Keyboard shortcuts settings page.
"""

import itertools

from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import (
    QAction, QComboBox, QHBoxLayout, QInputDialog, QKeySequence, QLabel,
    QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout)


from .. import (
    app,
    icons,
    preferences,
)

from ..widgets.shortcuteditdialog import ShortcutEditDialog


class Shortcuts(preferences.Page):
    def __init__(self, dialog):
        super(Shortcuts, self).__init__(dialog)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        top = QHBoxLayout()
        l = QLabel(_("Scheme:"))
        self.scheme = QComboBox()
        l.setBuddy(self.scheme)
        self.add = QPushButton(icons.get('list-add'), _("&Add..."))
        self.remove = QPushButton(icons.get('list-remove'), _("&Remove"))
        top.addWidget(l)
        top.addWidget(self.scheme)
        top.addWidget(self.add)
        top.addWidget(self.remove)
        layout.addLayout(top)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels([_("Command"), _("Shortcut")])
        self.tree.setRootIsDecorated(False)
        self.tree.setColumnCount(2)
        self.tree.setAllColumnsShowFocus(True)
        self.tree.setAnimated(True)
        layout.addWidget(self.tree)
        
        self.edit = QPushButton(icons.get("configure-shortcuts"), '')
        layout.addWidget(self.edit)
        
        # signals
        self.scheme.currentIndexChanged.connect(self.slotSchemeChanged)
        self.tree.currentItemChanged.connect(self.slotCurrentItemChanged)
        self.tree.itemDoubleClicked.connect(self.editCurrentItem)
        self.edit.clicked.connect(self.editCurrentItem)
        self.add.clicked.connect(self.addClicked)
        self.remove.clicked.connect(self.removeClicked)
        
        # make a dict of all actions with the actions as key and the names as
        # value, with the collection prepended (for loading/saving)
        win = dialog.mainwindow
        allactions = {}
        for collection in (
                win.actionCollection,
                win.viewManager.actionCollection,
                ):
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
            text = removeAccels(a.text())
            for a in childactions(menu):
                menuitem.addChild(ShortcutItem(a, *allactions[a]))
            if menuitem.childCount():
                menuitem.setText(0, _("Menu {name}:").format(name=text))
                self.tree.addTopLevelItem(menuitem)
                menuitem.setExpanded(True)
                menuitem.setFlags(Qt.ItemIsEnabled) # disable selection
                
        # show other actions that were not in the menus
        item = QTreeWidgetItem([_("Other commands:")])
        for a in left:
            if not a.menu():
                item.addChild(ShortcutItem(a, *allactions[a]))
        if item.childCount():
            self.tree.addTopLevelItem(item)
            item.setExpanded(True)
            item.setFlags(Qt.ItemIsEnabled) # disable selection
        
        self.tree.setCurrentItem(self.tree.topLevelItem(0).child(0))
        self.tree.resizeColumnToContents(0)
        
    def items(self):
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            for j in range(top.childCount()):
                yield top.child(j)
    
    def saveSettings(self):
        # first save new scheme names
        s = QSettings()
        for scheme, name in zip(self._schemes, self._schemeNames)[1:]:
            s.setValue("shortcut_schemes/" + scheme, name)
        # then save all the actions in all schemes
        for scheme in self._schemes:
            for item in self.items():
                item.save(scheme)
        # then remove removed schemes
        for scheme in self._schemesToRemove:
            s.remove("shortcut_schemes/" + scheme)
            s.remove("shortcuts/" + scheme)
        # then save current
        s.setValue("shortcut_scheme", self._schemes[self.scheme.currentIndex()])
        # clean up
        self._schemesToRemove = set()
        for item in self.items():
            item.clearSettings()
        
    def loadSettings(self):
        # dont mark schemes for removal anymore
        self._schemesToRemove = set()
        
        s = QSettings()
        cur = s.value("shortcut_scheme", "default")
        
        # load the names for the shortcut schemes
        s.beginGroup("shortcut_schemes")
        self._schemes = ["default"]
        self._schemeNames = [_("Default")]
        for key in s.childKeys():
            self._schemes.append(key)
            self._schemeNames.append(s.value(key, key))
        block = self.scheme.blockSignals(True)
        self.scheme.clear()
        self.scheme.addItems(self._schemeNames)
        s.endGroup()
        
        # find out index
        index = self._schemes.index(cur) if cur in self._schemes else 0
        self.remove.setEnabled(bool(index))
        
        # clear the settings in all the items
        for item in self.items():
            item.clearSettings()
            item.switchScheme(self._schemes[index])
        
        self.scheme.setCurrentIndex(index)
        self.scheme.blockSignals(block)
        
    def slotSchemeChanged(self, index):
        """Called when the Scheme combobox is changed by the user."""
        self.remove.setEnabled(bool(index))
        for item in self.items():
            item.switchScheme(self._schemes[index])
        self.changed()
        
    def slotCurrentItemChanged(self, item):
        if isinstance(item, ShortcutItem):
            self.edit.setText(
                "&Edit Shortcut for \"{name}\"".format(name=item.text(0)))
            self.edit.setEnabled(True)
        else:
            self.edit.setText(_("(no shortcut)"))
            self.edit.setEnabled(False)
        
    def editCurrentItem(self):
        item = self.tree.currentItem()
        if not isinstance(item, ShortcutItem):
            return
        try:
            dlg = self._editdialog
        except AttributeError:
            dlg = self._editdialog = ShortcutEditDialog(self)
        scheme = self._schemes[self.scheme.currentIndex()]
        action = item.action(scheme)
        default = item.defaultShortcuts()
        if dlg.editAction(action, default):
            
            # check for conflicts
            conflicting = []
            for i in self.items():
                if i is not item:
                    for s1, s2 in itertools.product(i.shortcuts(scheme), action.shortcuts()):
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
                            for s2 in action.shortcuts():
                                if s1.matches(s2) or s2.matches(s1):
                                    l.remove(s1)
                        i.setShortcuts(l, scheme)
                elif res == QMessageBox.No:
                    # remove from ourselves
                    l = action.shortcuts()
                    for i in conflicting:
                        for s1 in list(l): # copy
                            for s2 in i.shortcuts(scheme):
                                if s1.matches(s2) or s2.matches(s1):
                                    l.remove(s1)
                    action.setShortcuts(l)
                else:
                    return # cancelled
            # store the shortcut
            item.setShortcuts(action.shortcuts(), scheme)
            self.changed()

    def removeClicked(self):
        index = self.scheme.currentIndex()
        if index == 0:
            return # default can not be removed
        
        self._schemesToRemove.add(self._schemes[index])
        del self._schemes[index]
        del self._schemeNames[index]
        self.scheme.removeItem(index)
        self.changed()
    
    def addClicked(self):
        name, ok = QInputDialog.getText(self,
            app.caption("Add Scheme"),
            _("Please enter a name for the new scheme:"))
        if not ok:
            return
        num, key = 1, 'user1'
        while key in self._schemes or key in self._schemesToRemove:
            num += 1
            key = 'user{0}'.format(num)
        self._schemes.append(key)
        self._schemeNames.append(name)
        self.scheme.addItem(name)
        self.scheme.setCurrentIndex(self.scheme.count() - 1)
        self.changed()
        
        
class ShortcutItem(QTreeWidgetItem):
    def __init__(self, action, collection, name):
        QTreeWidgetItem.__init__(self)
        self.collection = collection
        self.name = name
        self.setIcon(0, action.icon())
        self.setText(0, removeAccels(action.text()))
        self.clearSettings()
        
    def clearSettings(self):
        self._shortcuts = {}
    
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
                self._shortcuts[scheme] = ([QKeySequence(v) for v in s.value(key) or []], False)
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
            text = shortcuts[0].toString()
            if len(shortcuts) > 1:
                text += "..."
            if default:
                text += "  " + _("(default)")
        self.setText(1, text)
        
        
def removeAccels(s):
    return s.replace('&&', '\0').replace('&', '').replace('\0', '&')


