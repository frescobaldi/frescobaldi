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
ActionCollection is a class to keep a list of actions as attributes.
"""

import weakref

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QKeySequence

import app


class ActionCollectionBase(object):
    """Abstract base class. Can load and keep a list of QActions."""
    def __init__(self, widget=None):
        self._widget = weakref.ref(widget) if widget else lambda: None
        self._actions = {}  # maps name to action
        self._defaults = {} # maps name to default list of shortcuts
    
    def widget(self):
        return self._widget()
        
    def setDefaultShortcuts(self, name, shortcuts):
        self._defaults[name] = shortcuts
        
    def settingsGroup(self):
        """Returns settings group to load shortcuts from."""
        s = QSettings()
        scheme = s.value("shortcut_scheme", "default")
        s.beginGroup("shortcuts/{0}/{1}".format(scheme, self.name))
        return s
        
    def actions(self):
        """Returns the dictionary with actions."""
        return self._actions
        
    def defaults(self):
        """Returns the dictionary with actions that have a default shortcut."""
        return self._defaults
        
    def names(self):
        """Returns the names of all actions."""
        return self._actions.keys()
        
    def text(self, name):
        """Returns the text of the named action, with ampersands removed."""
        return self._actions[name].text().replace('&&', '\0').replace('&', '').replace('\0', '&')

    def icon(self, name):
        """Returns the icon of the named action"""
        return self._actions[name].icon()
    

class ActionCollection(ActionCollectionBase):
    """Keeps a fixed list of QActions as instance attributes.
    
    Subclass this and add the actions as instance attributes in
    the createActions() method.
    
    """
    def __init__(self, parent=None):
        """Should define all actions in this collection as instance attributes."""
        super(ActionCollection, self).__init__(parent)
        self.createActions(parent)
        self._actions = dict(i for i in self.__dict__.items() if not i[0].startswith('_'))
        self.storeDefaults()
        self.load(False) # load the shortcuts without resettings defaults
        app.translateUI(self)
        app.settingsChanged.connect(self.load)
        
    def createActions(self, parent=None):
        """Should add actions as instance attributes.
        
        The QActions should get icons and shortcuts. Texts should be set
        in translateUI().
        
        """
        pass

    def translateUI(self):
        """Should (re)translate all the titles of the actions."""
        pass
    
    def storeDefaults(self):
        """Saves the preset default QKeySequence values for the actions."""
        for name, action in self._actions.items():
            if action.shortcuts():
                self.setDefaultShortcuts(name, action.shortcuts())

    def load(self, restoreDefaults=True):
        """Reads keyboard shortcuts from the settings.
        
        If restoreDefaults == True, resets the other shortcuts to their default
        values. If restoreDefaults == False, does not touch the other shortcuts.
        
        """
        settings = self.settingsGroup()
        keys = settings.allKeys()
        for name in keys:
            try:
                self._actions[name].setShortcuts([QKeySequence(s) for s in settings.value(name) or []])
            except KeyError:
                settings.remove(name)
        if restoreDefaults:
            for name in self._actions:
                if name not in keys:
                    self._actions[name].setShortcuts(self._defaults.get(name) or [])


class VariableActionCollection(ActionCollectionBase):
    """An ActionCollection type that only saves actions that have a keyboard shortcut.
    
    Should always be instantiated with the MainWindow as a parent.
    
    Use the setShortcuts() method to set a list (possibly empty) of QKeySequence
    objects.  Every change causes other instances of the sane-named collection
    to reload.
    
    This serves two purposes:
    1. save keyboard shortcuts for actions created by the user or from a very large list
    2. make the keyboard shortcuts working even if the component their actions are
       contained in is not even loaded yet.
       
       To make this work, implement the realAction() method to instantiate the widget the
       action is meant for and then return the real action.
       
    """
    # save weak references to other instances with the same name and sync then.
    others = {}
    
    def __init__(self, mainwindow):
        super(VariableActionCollection, self).__init__(mainwindow)
        self.createDefaults()
        self.load()
        app.settingsChanged.connect(self.load)
        self.others.setdefault(self.name, []).append(weakref.ref(self))
        
    def mainwindow(self):
        return self.widget()
        
    def createDefaults(self):
        """Should set some default shortcut lists using setDefaultShortcuts()."""
        pass
        
    def load(self):
        """Reads keyboard shortcuts from the settings.  Instantiates QActions as needed."""
        # clears all actions
        for a in self._actions.values():
            a.setParent(None)
        self._actions = {}
        # then set defaults
        for name, shortcuts in self.defaults().items():
            self.action(name).setShortcuts(shortcuts)
        # then load
        for name in self.settingsGroup().allKeys():
            shortcuts = [QKeySequence(s) for s in settings.value(name) or []]
            if not shortcuts and name not in self.defaults():
                self.remove(name)
    
    def shortcuts(name):
        """Returns the list of shortcuts for our action."""
        try:
            return self._actions[name].shortcuts()
        except KeyError:
            pass
        
    def setShortcuts(self, name, shortcuts):
        """Sets the shortcuts list for our action."""
        if not shortcuts and name not in self.defaults():
            self.remove(name)
        self.reloadOthers()
        
    def remove(self, name):
        try:
            self._actions[name].setParent(None)
            del self._actions[name]
        except KeyError:
            pass
        else:
            self.settingsGroup().remove(name)

    def action(self, name):
        """Returns a QAction for the name, instantiating it if necessary."""
        try:
            a = self._actions[name]
        except KeyError:
            a = self._actions[name] = QAction(self.mainwindow())
            a.triggered.connect(lambda: self.realAction(name).trigger())
        return a

    def realAction(self, name):
        """Implement this to return the real action the name refers to,
        
        This is called when the text and icon are needed (e.g. when the shortcut
        dialog is opened) or when our "shadow" action keyboard shortcut is triggered.
        
        The function may return None, e.g. when the action our name refers to does
        not exist anymore.  In that case our action is also removed.
        
        """
        pass
    
    def actions(self):
        """Returns our real actions instead of the shadow ones."""
        d = {}
        changed = False
        for name in list(self._actions):
            a = self.realAction(name)
            if a:
                d[name] = a
            else:
                changed = True
                self.remove(name)
        if changed:
            self.reloadOthers()
        return d
    
    def reloadOthers(self):
        for ref in self.others[self.name][:]:
            other = ref()
            if not other:
                self.others[self.name].remove(ref)
            elif other is not self:
                other.load()


def removeShortcut(action, key):
    """Removes matching QKeySequence from the list of the action."""
    key = QKeySequence(key)
    shortcuts = action.shortcuts()
    for s in action.shortcuts():
        if key.matches(s) or s.matches(key):
            shortcuts.remove(s)
    action.setShortcuts(shortcuts)


