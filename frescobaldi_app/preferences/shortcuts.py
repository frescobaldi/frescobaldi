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

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
    preferences,
)

from ..widgets.keysequencewidget import KeySequenceWidget



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
        layout.addWidget(self.tree)
        
        self.edit = QPushButton(icons.get("configure-shortcuts"), '')
        layout.addWidget(self.edit)
        
        # signals
        self.scheme.currentIndexChanged.connect(self.slotSchemeChanged)
        self.tree.currentItemChanged.connect(self.slotCurrentItemChanged)
        self.tree.itemDoubleClicked.connect(self.editCurrentItem)
        self.edit.clicked.connect(self.editCurrentItem)
        
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
    
    def loadSettings(self):
        s = QSettings()
        cur = s.value("shortcut_scheme", "default")
        
        # load the names for the shortcut schemes
        s.beginGroup("shortcut_schemes")
        self._schemes = ["default"]
        self._schemeNames = [_("Default")]
        for key in s.childKeys():
            self._schemes.append(key)
            self._schemeNames.append(s.value(key, key))
        self.scheme.clear()
        self.scheme.addItems(self._schemeNames)
        s.endGroup()
        
        # clear the settings in all the items
        for item in self.items():
            item.clearSettings()
        
        index = self._schemes.index(cur) if cur in self._schemes else 0
        block = self.scheme.blockSignals(True)
        self.scheme.setCurrentIndex(index)
        self.scheme.blockSignals(block)
        self.slotSchemeChanged(index)
        
    def slotSchemeChanged(self, index):
        """Called when the Scheme combobox is changed."""
        for item in self.items():
            item.switchScheme(self._schemes[index])
            
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
            item.setShortcuts(action.shortcuts(), scheme)


class ShortcutItem(QTreeWidgetItem):
    def __init__(self, action, collection, name):
        QTreeWidgetItem.__init__(self)
        self.collection = collection
        self.name = name
        self.setIcon(0, action.icon())
        self.setText(0, removeAccels(action.text()))
        self.clearSettings()
        
    def clearSettings(self):
        self.shortcuts = {}
    
    def action(self, scheme):
        """Returns a new QAction that represents our item.
        
        The action contains the text, icon and current shortcut.
        
        """
        action = QAction(self.icon(0), self.text(0), None)
        action.setShortcuts(self.shortcuts[scheme][0])
        return action
    
    def setShortcuts(self, shortcuts, scheme):
        print shortcuts, self.defaultShortcuts()
        default = shortcuts == self.defaultShortcuts()
        self.shortcuts[scheme] = (shortcuts, default)
        self.display(scheme)
        
    def defaultShortcuts(self):
        """Returns a (possibly empty) list of QKeySequence objects.
        
        The list represents the default shortcut for this item, if any.
        
        """
        return self.collection.defaults().get(self.name, [])
        
    def switchScheme(self, scheme):
        if scheme not in self.shortcuts:
            s = QSettings()
            key = "shortcuts/{0}/{1}/{2}".format(scheme, self.collection.name, self.name)
            if s.contains(key):
                self.shortcuts[scheme] = (s.value(key) or [], False)
            else:
                # default
                self.shortcuts[scheme] = (self.defaultShortcuts(), True)
        self.display(scheme)
        
    def display(self, scheme):
        text = ''
        shortcuts, default = self.shortcuts[scheme]
        if shortcuts:
            text = shortcuts[0].toString()
            if len(shortcuts) > 1:
                text += "..."
            if default:
                text += " " + _("(default)")
        self.setText(1, text)
        
        
def removeAccels(s):
    return s.replace('&&', '\0').replace('&', '').replace('\0', '&')


class ShortcutEditDialog(QDialog):
    """A modal dialog to view and/or edit keyboard shortcuts."""
    
    def __init__(self, parent=None):
        super(ShortcutEditDialog, self).__init__(parent)
        
        # create gui
        layout = QGridLayout()
        self.setLayout(layout)
        l = self.toplabel = QLabel()
        l.setWordWrap(True)
        l.setAlignment(Qt.AlignCenter)
        layout.addWidget(l, 0, 0, 1, 2)
        
        self.buttonDefault = QRadioButton(self)
        self.buttonNone = QRadioButton(_("No shortcut"), self)
        self.buttonCustom = QRadioButton(_("Use a custom shortcut:"), self)
        layout.addWidget(self.buttonDefault, 1, 0)
        layout.addWidget(self.buttonNone, 2, 0)
        layout.addWidget(self.buttonCustom, 3, 0)
        
        self.keybuttons = []
        for num in range(4):
            l = QLabel(_("Alternative #{num}:").format(num=num) if num else _("Primary shortcut:"))
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            b = KeySequenceWidget(self)
            l.setBuddy(b)
            self.keybuttons.append(b)
            layout.addWidget(l, num+4, 0)
            layout.addWidget(b, num+4, 1)
        
        b = QDialogButtonBox(self)
        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(b, 8, 0, 1, 2)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        
    def editAction(self, action, default=None):
        # load the action
        self._action = action
        self._default = default
        self.setWindowTitle(app.caption(
            _("Shortcut for \"{name}\"").format(name=action.text())))
        self.toplabel.setText(_(
            "Here you can view and/or edit the keyboard shortcuts "
            "for \"{name}\".").format(name=action.text()))
        shortcuts = action.shortcuts()
        if default is not None and shortcuts == default:
            self.buttonDefault.setChecked(True)
        elif shortcuts:
            self.buttonCustom.setChecked(True)
        else:
            self.buttonNone.setChecked(True)
        for num, key in enumerate(shortcuts[:4]):
            self.keybuttons[num].setShortcut(key)
        for num in range(len(shortcuts), 4):
            self.keybuttons[num].clear()
        ds = _("none") if not default else "; ".join(key.toString() for key in default)
        self.buttonDefault.setText(_("Use default shortcut ({name})").format(name=ds))
        
        return self.exec_()
        
    def done(self, result):
        if result:
            shortcuts = []
            if self.buttonDefault.isChecked():
                shortcuts = self._default
            elif self.buttonCustom.isChecked():
                for num in range(4):
                    if self.keybuttons[num].text() != "(empty)": # TEMP
                        shortcuts.append(QKeySequence(self.keybuttons[num].text()))
            self._action.setShortcuts(shortcuts)
        super(ShortcutEditDialog, self).done(result)

