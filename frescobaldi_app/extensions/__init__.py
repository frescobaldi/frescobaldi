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

from PyQt5.QtCore import Qt, QDir, QObject, QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu

import app
import icons
from . import actions

class ExtensionSettings(QSettings):
    """
    Base class to be used for storing extension settings.
    """
    def __init__(self):
        super(ExtensionSettings, self).__init__()
        self.beginGroup('extensions')

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

    # Can be defined in subclasses to create a Tool panel.
    # If a class is provided for a panel widget a Tool panel is
    # automatically created. By default the initial dock area is
    # the left dock area, but this can also be specified by
    # overriding the corresponding class variable.
    _panel_widget_class = None
    _panel_dock_area = Qt.LeftDockWidgetArea

    # Can be defined in subclasses to provide a configuration widget.
    # If this is present it will be shown in the Preferences page.
    # Config widgets can be any QWidget descendants, but must fulfill
    # some requirements:
    # - They have to  implement the loadSettings() and saveSettings() methods.
    # - Instead of a QSettings() object they should use
    #   extensions.ExtensionSettings() which ensures the settings are not
    #   mixed with Frescobaldi's own settings
    # - Any changes that have to be "applied" (i.e. that should enable
    #   the "Apply" button) must the emit self.parent().changed signal.
    _config_widget_class = None

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
        self._name = parent._current_extension
        self._action_collection =  self._action_collection_class(self)
        self._menus = {}
        self._panel = None
        self._config_widget = None
        self._icon = None
        self._load_icon()
        self.create_panel()

        # Hook that can be implemented to update extension status
        # after settings change.
        app.settingsChanged.connect(self.app_settings_changed)

    def action_collection(self):
        """Return the extension's action collection."""
        return self._action_collection

    def app_settings_changed(self):
        """Implement to respond to settings changes
        (e.g. to update GUI or action status)."""
        pass

    def config_widget(self, preference_group):
        """Return a config widget if provided by the extension, or None.
        Do *not* use caching (this is done in the Preferences group),
        and set the preference group as the widget's parent."""
        if not self._config_widget_class:
            return None
        widget = self._config_widget_class(preference_group)
        return widget

    def create_panel(self):
        """Create the Extension's Tool Panel if a widget class is provided.
        """
        if self._panel_widget_class:
            from . import panel
            self._panel = panel.ExtensionPanel(
                self,
                self._panel_widget_class,
                self._panel_dock_area)

    def display_name(self):
        """Return the display name of the extension.
        Should be overridden in concrete classes,
        class name is just a fallback."""
        return self.__class__._display_name

    def has_icon(self):
        return self._icon is not None

    def icon(self):
        """Return the extension's Icon, or None."""
        return self._icon

    def _load_icon(self):
        """Tries to load a main icon for the extension if
        <extension-dir>/icons/extension.svg exists.
        """
        icon_file_name = os.path.join(
            self.root_directory(), 'icons', 'extension.svg')
        if os.path.exists(icon_file_name):
            self._icon = QIcon(icon_file_name)

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
            if self.has_icon():
                m.setIcon(self.icon())
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

    def name(self):
        """Return the extension's internal name (which actually is retrieved
        from the directory name)."""
        return self._name

    def panel(self):
        """Return the extension's Tool panel, if available, None otherwise."""
        return self._panel

    def root_directory(self):
        """Return the extension's root directory."""
        return os.path.join(self.parent().root_directory(), self.name())

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
        self._active = False

        self._menus = {}
        self._extensions = {}
        # TODO: Handle app.settingsChanged
        self.load_settings()
        self._load_extensions()
        app.settingsChanged.connect(self.settings_changed)

    def active(self):
        """Returns True if extensions are enabled globally."""
        return self._active

    def _load_extensions(self):
        if not self.active():
            return
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
                # Try importing the module. Will fail here if there's
                # no Python module in the subdirectory.
                module = importlib.import_module(d)
                # Add extension's icons dir (if present) to icon search path
                search_paths = QDir.searchPaths('icons')
                icon_path = os.path.join(self.root_directory(), d, 'icons')
                if os.path.isdir(icon_path):
                    QDir.setSearchPaths('icons', [icon_path] + search_paths)
                # temporary reference to store the _name in the Extension
                self._current_extension = d
                # Instantiate the extension,
                # this will fail if the module is no valid extension
                self._extensions[d] = module.Extension(self)
            except AttributeError as e:
                #TODO: Can this be logged instead of print()-ed?
                print("Not a valid Frescobaldi extension: '{}\n'. Reason:\n".format(d))
                print(e)
                print()
        del self._current_extension

    def extensions(self):
        """Return the extensions as a list."""
        result = [self._extensions[ext] for ext in self._extensions.keys()]
        result.sort(key=lambda extension: extension.display_name())
        return result

    def get(self, module_name):
        """Return an Extension object for an extension with the given name,
        or None if such a module doesn't exist."""
        return self._extensions.get(module_name, None)

    def load_settings(self):
        s = QSettings()
        s.beginGroup('extension-settings')
        self._active = s.value('active', True, bool)
        self._root_directory = s.value('root-directory', '', str)

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
            m.setIcon(icons.get('network-plug'))
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
        s.beginGroup('extension-settings')
        active = s.value('active', True, bool)
        root = s.value('root-directory', '', str)
        if (
            active != self.active()
            or root != self.root_directory()
        ):
            from widgets.restartmessage import suggest_restart
            suggest_restart(_('Something with the extensions'))
