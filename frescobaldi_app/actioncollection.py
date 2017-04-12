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
In this module are two classes, ActionCollection and ShortcutCollection.
Both must be inherited to do something useful.

ActionCollection keeps a fixed list of QActions, set as instance attributes in
the createActions() method. The icons and default shortcuts may also be set in
the same method. The texts should be set in the translateUI() method.

The ActionCollection then keeps track of possibly changed keyboard shortcuts by
loading them from the config and connecting to the app.settingsChanged() signal.

ShortcutCollection keeps a variable list of QActions, for which default
shortcuts must be set in the createDefaultShortcuts() method.

This actions must not be connected to, but they are only used to set keyboard
shortcuts for a module that needs not to be loaded initially for the shortcuts
to work. If a shortcut is pressed, the real action is queried using the
realAction() method, which should return the corresponding action in the UI.
That one is than triggered.

The module may provide the user with a means to change the keyboard shortcuts,
which then should call setShortcuts() to do it. The module may also query the
currently set shortcuts for an action using shortcuts().
"""


import weakref

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import app


class ActionCollectionBase(object):
    """Abstract base class. Can load and keep a list of QActions.

    You must subclass this class and provide a name for the actioncollection
    in the 'name' class attribute.

    """
    def __init__(self, widget=None):
        self._widget = weakref.ref(widget) if widget else lambda: None
        self._actions = {}  # maps name to action
        self._defaults = {} # maps name to default list of shortcuts
        app.settingsChanged.connect(self.load)

    def widget(self):
        """Returns the widget given on construction or None."""
        return self._widget()

    def setDefaultShortcuts(self, name, shortcuts):
        """Set a default list of QKeySequence objects for the named action."""
        self._defaults[name] = shortcuts

    def defaultShortcuts(self, name):
        """Returns the default shortcuts (list of QKeySequences) for the action.

        If not defined, returns None.

        """
        return self._defaults.get(name)

    def actions(self):
        """Returns the dictionary with actions."""
        return self._actions

    def defaults(self):
        """Returns the dictionary with actions that have a default shortcut."""
        return self._defaults

    def shortcuts(self, name):
        """Returns the list of shortcuts for the named action, or None."""
        try:
            return self._actions[name].shortcuts()
        except KeyError:
            pass

    def setShortcuts(self, name, shortcuts):
        """Implement to set the shortcuts list for our action."""
        pass

    def settingsGroup(self):
        """Returns settings group to load/save shortcuts from or to."""
        s = QSettings()
        scheme = s.value("shortcut_scheme", "default", str)
        s.beginGroup("shortcuts/{0}/{1}".format(scheme, self.name))
        return s

    def load(self):
        """Implement to load shortcuts from our settingsGroup()."""
        pass

    def title(self):
        """If this returns a meaningful title, actions can be grouped in the shortcut settings dialog."""
        pass


class ActionCollection(ActionCollectionBase):
    """Keeps a fixed list of QActions as instance attributes.

    Subclass this and add the actions as instance attributes in
    the createActions() method.

    You can set the default shortcuts directly in the actions in the
    createActions() method, it is not needed to use the setDefaultShortcuts()
    method for that.

    Set the titles for the actions in the translateUI() method.

    """
    def __init__(self, parent=None):
        """Creates the ActionCollection.

        parent is an optional widget that is also the parent for the created actions.

        """
        super(ActionCollection, self).__init__(parent)
        self.createActions(parent)
        self._actions = dict(i for i in self.__dict__.items() if not i[0].startswith('_'))
        self.storeDefaults()
        self.load(False) # load the shortcuts without resettings defaults
        app.translateUI(self)

    def createActions(self, parent=None):
        """Should add actions as instance attributes.

        The QActions should get icons and shortcuts. Texts should be set
        in translateUI(). The actions are created with the parent given on instantiation.

        """
        pass

    def translateUI(self):
        """Should (re)translate all the titles of the actions."""
        pass

    def storeDefaults(self):
        """Saves the preset default QKeySequence lists for the actions."""
        for name, action in self._actions.items():
            if action.shortcuts():
                self.setDefaultShortcuts(name, action.shortcuts())

    def setShortcuts(self, name, shortcuts):
        """Sets the shortcuts list for our action. Use an empty list to remove the shortcuts."""
        action = self.actions().get(name)
        if not action:
            return

        default = self.defaultShortcuts(name)
        setting = self.settingsGroup()
        action.setShortcuts(shortcuts)
        setting.setValue(name, shortcuts)
        if default:
            if shortcuts == default:
                setting.remove(name)
            else:
                setting.setValue(name, shortcuts)
        else:
            if shortcuts:
                setting.setValue(name, shortcuts)
            else:
                setting.remove(name)

    def load(self, restoreDefaults=True):
        """Reads keyboard shortcuts from the settings.

        If restoreDefaults == True, resets the other shortcuts to their default
        values. If restoreDefaults == False, does not touch the other shortcuts.

        """
        settings = self.settingsGroup()
        keys = settings.allKeys()
        for name in keys:
            try:
                shortcuts = settings.value(name, [], QKeySequence)
            except TypeError:
                # PyQt5 raises TypeError when an empty list was stored
                shortcuts = []
            try:
                self._actions[name].setShortcuts(shortcuts)
            except KeyError:
                settings.remove(name)
        if restoreDefaults:
            for name in self._actions:
                if name not in keys:
                    self._actions[name].setShortcuts(self._defaults.get(name) or [])


class ShortcutCollection(ActionCollectionBase):
    """An ActionCollection type that only saves actions that have a keyboard shortcut.

    Should always be instantiated with a visible widget (preferably MainWindow)
    as parent.

    Use the setShortcuts() method to set a list (possibly empty) of QKeySequence
    objects.  Every change causes other instances of the same-named collection
    to reload.

    This serves two purposes:
    1. save keyboard shortcuts for actions created by the user or from a very large list
    2. make the keyboard shortcuts working even if the component the actions are
       contained in is not even loaded yet.

       To make this work, implement the realAction() method to instantiate the widget the
       action is meant for and then return the real action.

    """
    # save weak references to other instances with the same name and sync then.
    others = {}

    # shortcut context to use by default
    shortcutContext = Qt.WindowShortcut

    def __init__(self, widget):
        """Creates the ShortcutCollection.

        The widget is required as actions are added to it, so their keyboard
        shortcuts get triggered.

        """
        super(ShortcutCollection, self).__init__(widget)
        self.createDefaultShortcuts()
        self.load()
        self.others.setdefault(self.name, []).append(weakref.ref(self))

    def createDefaultShortcuts(self):
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
        settings = self.settingsGroup()
        for name in settings.allKeys():
            try:
                shortcuts = settings.value(name, [], QKeySequence)
            except TypeError:
                # PyQt5 raises TypeError when an empty list was stored
                shortcuts = []
            if not shortcuts:
                if not self.removeAction(name):
                    # if it did not exist, remove key from config
                    settings.remove(name)
            else:
                self.action(name).setShortcuts(shortcuts)

    def setShortcuts(self, name, shortcuts):
        """Sets the shortcuts list for our action. Use an empty list to remove the shortcuts."""
        if shortcuts:
            self.action(name).setShortcuts(shortcuts)
            self.settingsGroup().setValue(name, shortcuts)
        else:
            self.removeAction(name)
            if name in self.defaults():
                # save empty list because there exists a default value
                self.settingsGroup().setValue(name, [])
            else:
                self.settingsGroup().remove(name)
        self.reloadOthers()

    def restoreDefaultShortcuts(self, name):
        """Resets the shortcuts for the specified action to their default value."""
        shortcuts = self.defaultShortcuts(name)
        if shortcuts:
            self.action(name).setShortcuts(shortcuts)
        else:
            self.removeAction(name)
        self.settingsGroup().remove(name)
        self.reloadOthers()

    def removeAction(self, name):
        """(Internal) Removes the named action, returning True it it did exist."""
        try:
            a = self._actions[name]
        except KeyError:
            return False
        a.setParent(None)
        del self._actions[name]
        return True

    def action(self, name):
        """Returns a QAction for the name, instantiating it if necessary."""
        try:
            a = self._actions[name]
        except KeyError:
            a = self._actions[name] = QAction(self.widget())
            a.setShortcutContext(self.shortcutContext)
            a.triggered.connect(lambda: self.triggerAction(name))
            self.widget().addAction(a)
        return a

    def triggerAction(self, name):
        """Called when the user presses a saved keyboard shortcut."""
        a = self.realAction(name)
        if a:
            a.trigger()

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
                self.removeAction(name)
                changed = True
        if changed:
            self.reloadOthers()
        return d

    def reloadOthers(self):
        """Reload others managing the same shortcuts (e.g. in case of multiple mainwindows)."""
        for ref in self.others[self.name][:]:
            other = ref()
            if not other:
                self.others[self.name].remove(ref)
            elif other is not self:
                other.load()


