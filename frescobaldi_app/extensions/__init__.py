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
The extensions framework
"""

import importlib
import os
import sys

from PyQt5.QtCore import QObject, QSettings
from PyQt5.QtWidgets import QMenu

import app
from . import actions

class Extension(QObject):
    """
    Base class for all Extension objects.
    Ensures integration in the Tools menu and other places,
    and provides common APIs both for the extension to
    access resources and for the application to interact
    with the extention.

    An Extension provides a number of convenience functions to
    objects that could also be retrieved through other means,
    but we want to provide a convenient API for extension development.
    They can be found at the end of this implementation.
    """

    # To be defined in subclasses,
    # used for the Tools menu submenu title and (later)
    # in the Preferences page.
    _display_name = "Display name of extension not specified"

    # To be defined in subclasses,
    # specify a class for the extension's action collection.
    # If no action collection class is given the default
    # action collection will be empty, which *may* be
    # desired if an extension only wants to provide a Tool panel.
    _action_collection_class = actions.ExtensionActionCollection

    def __init__(self, parent):
        """Initialize (load) the extension.
        NOTE: This loading takes place at program start, so
        any concrete extension should take care to load its
        resources (dialogs etc.) only upon use. During __init__
        only the actions and the optional Tool panel should be
        created.
        The parent argument points to the global Extensions object."""
        assert issubclass(
            self._action_collection_class, actions.ExtensionActionCollection)
        super(Extension, self).__init__(parent)
        self._action_collection =  self._action_collection_class(
            parent.mainwindow())
        self._menus = {}
        self._panel = None
        self.create_panel()

    def action_collection(self):
        """Return the extension's action collection."""
        return self._action_collection

    def create_panel(self):
        """Create the Extension's Tool Panel (optional).

        If a Tool Panel has been configured through the use of
        self.set_panel_properties() in a subclass's __init__()
        an appropriate Panel is created.
        """
        if hasattr(self, "_panel_conf"):
            from . import panel
            self._panel = panel.ExtensionPanel(self)

    def display_name(self):
        """Return the display name of the extension.
        Should be overridden in concrete classes,
        class name is just a fallback."""
        return self.__class__._display_name

    def menu(self, target):
        """Return a submenu for use in an Extensions menu,
        or None if there should be no entry for the given target.
        target may be 'tools' for the main Tools=>Extensions menu,
        or a known keyword for one of the context menus (see
        __init__ for the available keys).

        If the target is 'tools' and the extension exports a Panel
        then this will be inserted at the top of the menu, otherwise
        only the action list will be used to create the menu.
        The various menus can be configured in the action collection,
        by default the tools menu shows all actions, sorted by
        display name, and context menus are empty.
        """
        m = self._menus.get(target, None)
        if not m:
            actions = self.action_collection().menu_actions(target)
            if target != 'tools' and not actions:
                # empty context menu
                return None
            panel = self.panel()
            # An extension without at least one action or panel
            # is invalid
            if not (panel or actions):
                m = QMenu(_("Invalid extension: {}".format(
                    self.display_name())))
                return m

            # finally create the menu
            m = self._menus[target] = QMenu(
                self.display_name(), self.mainwindow())
            if panel and target == 'tools':
                panel.toggleViewAction().setText(_("&Tool Panel"))
                m.addAction(panel.toggleViewAction())
                if actions:
                    m.addSeparator()
            for entry in actions:
                if isinstance(entry, QMenu):
                    m.addMenu(entry)
                else:
                    m.addAction(entry)
        return m

    def panel(self):
        """Return the extension's Tool panel, if available, None otherwise."""
        return self._panel

    def set_panel_properties(self, widget_class, dock_area):
        """Specify an Extension Panel to be created.
        If this method is called in the subclass's __init__() a
        Panel will be created.
        The widget class and the (initial) dock area are the only
        custom parameters of an Extension Panel, everything else
        will be transparently generated."""
        self._panel_conf = {
            'widget_class': widget_class,
            'dock_area': dock_area
        }

    # Convenience functions to access elements of the application
    # and the current documents. This will be extended.

    def current_document(self):
        """Returns the currently opened document or None."""
        return self.mainwindow().currentDocument()

    def mainwindow(self):
        """Returns a reference to the main window."""
        return self.parent().mainwindow()

    def text_cursor(self):
        """The text cursor of the current document."""
        return self.mainwindow().textCursor()


class Extensions(QObject):
    """Global object managing the extensions.
    Accessed with app.extensions()"""

    def __init__(self, mainwindow):
        super(Extensions, self).__init__()
        self._mainwindow = mainwindow
        self._root_directory = None

        self._menus = {}
        self._extensions = {}
        # TODO: Handle app.settingsChanged
        self.load_settings()
        self._load_extensions()
        app.settingsChanged.connect(self.settings_changed)

#        self.unload_extensions()

    def _load_extensions(self):
        root = self.root_directory()
        if not (root and os.path.isdir(root)):
            return
        self._extensions = {}
        if not root in sys.path:
            sys.path.append(root)
        subdirs = os.listdir(root)
        for d in subdirs:
            # TODO: Check against a list of deactivated extensions
            # TODO (maybe:) allow manual order of loading
            #               (to handle dependency issues)
            try:
                module = importlib.import_module(d)
                self._extensions[d] = module.Extension(self)
            except AttributeError as e:
                #TODO: Can this be logged instead of print()-ed?
                print("Not a valid Frescobaldi extension: '{}\n'. Reason:\n".format(d))
                print(e)
                print()

    def extensions(self):
        """Return the extensions as a list."""
        #TODO: sort by display name, or custom ordering from Preferences
        return [self._extensions[ext] for ext in self._extensions.keys()]

    def get(self, module_name):
        """Return an Extension object for an extension with the given name,
        or None if such a module doesn't exist."""
        return self._extensions.get(module_name, None)

    def load_settings(self):
        s = QSettings()
        s.beginGroup('extensions')
        self._root_directory = s.value('general/root', '', str)
        self._active = s.value('general/active', True, bool)

    def mainwindow(self):
        """Reference to the main window."""
        return self._mainwindow

    def menu(self, target):
        """Create and return a nested Extensions menu,
        used for the Tools menu or context menus."""

        m = self._menus.get(target, None)
        if not m:
            #TODO: Create mnemonics for the menu entries
            m = self._menus[target] = QMenu(_("&Extensions"), self.mainwindow())
            for ext in self.extensions():
                ext_menu = ext.menu(target)
                if ext_menu:
                    m.addMenu(ext_menu)
        return m

    def root_directory(self):
        """Root directory below which extensions are searched for."""
        return self._root_directory

    def set_tools_menu(self, menu):
        """Store a reference to the global Tools menu."""
        self._tools_menu = menu

    def settings_changed(self):
        s = QSettings()
        s.beginGroup('extensions')

        #TODO: Handle 'active' preference

        root = s.value('general/root', '', str)
        if root != self.root_directory():
            self.unload_extensions()
            self._root_directory = root
            self._load_extensions()
            menu = self.menu('tools')
            if not menu.isEmpty():
                self._tools_menu.addSeparator()
                self._tools_menu.addMenu(menu)

    def unload_extensions(self):
        self._tools_menu.removeAction(self.menu('tools').menuAction())
        # TODO: I think the QMenu-s should explicitly be deleted?
        self._menus = {}
        # TODO: Probably this should be made more thorough,
        # doing proper clean-up?
        for ext in self._extensions.values():
            ext.panel().close()
        self._extensions = {}
