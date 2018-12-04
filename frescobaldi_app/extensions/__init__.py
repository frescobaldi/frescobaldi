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
from time import perf_counter

from PyQt5.QtCore import Qt, QDir, QObject, QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu

import app
import icons
import vbcl
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
        self._metadata = None
        self._load_time = ''
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
        metadata = self.parent().infos()[self.name()]
        return metadata['extension-name'] if metadata else _("Failed to load info")

    def has_icon(self):
        return self.icon() is not None

    def icon(self):
        """Return the extension's Icon, or None."""
        return self.parent().icon(self.name())

    def infos(self):
        """Return the infos dictionary for the extension,
        or an empty dictionary if they could not be loaded."""
        return self.parent().infos()[self.name()] or {}

    def load_time(self):
        """Return the loading time for the Extension object, formatted
        as a string with milliseconds."""
        return self._load_time

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

    def set_load_time(self, ms):
        """Store the time needed to load the application.
        A string with two fractional digits in 'ms'."""
        self._load_time = ms

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

    api_version = (0, 5, 0)

    def __init__(self, mainwindow):
        super(Extensions, self).__init__()
        self._mainwindow = mainwindow
        self._config_widgets = None
        self._menus = {}
        self._icons = {}
        self._infos = {}
        self._failed_infos = {}
        self._extensions = {}
        self._extensions_ordered = []
        self._failed_extensions = {}
        self._failed_dependencies = []

        # These two will be set in load_settings()
        self._root_directory = None
        self._active = False
        self._inactive_extensions = []
        self.load_settings()
        app.settingsChanged.connect(self.settings_changed)
        self.load_infos()
        if (self.active()
            and self.root_directory()
            and os.path.isdir(self.root_directory())):
            self.check_dependencies()
            if not self._failed_dependencies:
                self.load_extensions()
        if (self._failed_infos
            or self._failed_extensions
            or self._failed_dependencies):
            self.report_failed()


    def active(self):
        """Returns True if extensions are enabled globally."""
        return self._active

    def check_dependencies(self):
        """Check infos for unresolved or circular dependencies,
        order etensions to be loaded in topological order."""
        inactive = self.inactive_extensions()
        active = [key for key in self._infos.keys() if not key in inactive]
        inactive_dependencies = []
        missing_dependencies = []
        infos = self._infos
        nodes = {}
        incoming = {}
        no_incoming = {}
        result = []

        # Create topological order (and check for cyclic dependencies)
        # by Kahn's algorithm
        for ext in self._infos.keys():
            nodes[ext] = { 'incoming': [], 'outgoing': [] }
        # read incoming dependencies,
        # check for missing or deactivated dependencies.
        for ext in self._infos.keys():
            info = infos[ext]
            if not info:
                continue
            deps = info['dependencies']
            if deps == '---':
                continue
            for dep in deps:
                if dep in self._infos.keys(): #active + inactive:
                    nodes[dep]['incoming'].append(ext)
                    nodes[ext]['outgoing'].append(dep)
                    if dep in inactive:
                        inactive_dependencies.append((ext, dep))
                else:
                    missing_dependencies.append((ext, dep))

        # Create initial set/queue of nodes with no incoming edges
        for n in nodes:
            if nodes[n]['incoming']:
                incoming[n] = nodes[n]
            else:
                no_incoming[n] = nodes[n]
        nodes = None

        # Process queue until empty
        while no_incoming:
            ext = list(no_incoming.keys())[0]
            node = no_incoming.pop(ext)
            result.append(ext)
            # Process nodes ext depends on
            for outgoing in node['outgoing']:
                target_node = incoming[outgoing]
                # Remove egde
                target_node['incoming'].remove(ext)
                # If target has no more incoming edges, move to queue
                if not target_node['incoming']:
                    no_incoming[outgoing] = incoming.pop(outgoing)

        if missing_dependencies or inactive_dependencies or incoming:
            message = []
            if missing_dependencies:
                message.append(_("\nMissing dependencies:"))
                for dep in missing_dependencies:
                    message.append("   {} => {}".format(dep[0], dep[1]))
            if inactive_dependencies:
                message.append(_("\nDeactivated dependencies:"))
                for dep in inactive_dependencies:
                    message.append("   {} => {}".format(dep[0], dep[1]))
            if incoming:
                # If there remain incoming edges we have a
                # circular depencency (according to Kahn's algorithm)
                message.append(_("\nCircular dependencies involving:"))
                for ext in incoming.keys():
                    message.append("   - {}".format(ext))
            self._failed_dependencies = message
        else:
            self._extensions_ordered = reversed(result)

    def load_extensions(self):
        root = self.root_directory()
        if not root in sys.path:
            sys.path.append(root)

        for ext in self._extensions_ordered:
            try:
                start = perf_counter()
                # temporary reference to store the _name in the Extension
                self._current_extension = ext
                # Try importing the module. Will fail here if there's
                # no Python module in the subdirectory.
                module = importlib.import_module(ext)
                # Add extension's icons dir (if present) to icon search path
                search_paths = QDir.searchPaths('icons')
                icon_path = os.path.join(self.root_directory(), ext, 'icons')
                if os.path.isdir(icon_path):
                    QDir.setSearchPaths('icons', [icon_path] + search_paths)
                # Instantiate the extension,
                # this will fail if the module is no valid extension
                extension = module.Extension(self)
                end = perf_counter()
                extension.set_load_time(
                    "{:.2f} ms".format((end - start) * 1000))
                self._extensions[ext] = extension
            except Exception as e:
                self._failed_extensions[ext] = sys.exc_info()
            finally:
                del self._current_extension

    def _load_icon(self, name):
        """Tries to load a main icon for the given extension if
        <extension-dir>/icons/extension.svg exists.
        """
        icon_file_name = os.path.join(
            self.root_directory(), name, 'icons', 'extension.svg')
        self._icons[name] = (
            QIcon(icon_file_name) if os.path.exists(icon_file_name) else None)

    def icon(self, name):
        """Return a main icon for the given extension, or None."""
        icon = self._icons.get(name, False)
        if icon == False: # different from None, which may be a valid result
            self._load_icon(name)
        return self._icons[name]

    def _load_infos(self, extension_name):
        # Mandatory keys in the extension.cfg file
        mandatory_config_keys = [
            'extension-name',
            'maintainers',
            'version',
            'api-version',
            'license'
        ]
        # Default values for accepted config keys
        config_defaults = {
            'short-description': '',
            'description': '',
            'repository': '',
            'website': '',
            'dependencies': '---'
        }
        config_file = os.path.join(
            self.root_directory(), extension_name, 'extension.cnf')
        try:
            return vbcl.parse_file(
                config_file,
                mandatory_keys=mandatory_config_keys,
                defaults=config_defaults)
        except Exception as e:
            self._failed_infos[extension_name] = str(e)

    def load_infos(self):
        root = self.root_directory()
        subdirs = [dir for dir in os.listdir(root) if os.path.isfile(
            os.path.join(root, dir, 'extension.cnf'))]
        for d in subdirs:
            try:
                self._infos[d] = self._load_infos(d)
            except Exception as e:
                pass

    def config_widgets(self, preference_group):
        """Return a dictionary with config widgets.
        Will be created upon first request."""
        if self._config_widgets is None:
            self._config_widgets = {}
            for ext in self.extensions():
                widget = ext.config_widget(preference_group)
                if widget:
                    widget.hide()
                    self._config_widgets[ext.name()] = widget
        return self._config_widgets

    def extensions(self):
        """Return the extensions as a list."""
        result = [self._extensions[ext] for ext in self._extensions.keys()]
        result.sort(key=lambda extension: extension.display_name())
        return result

    def failed(self):
        return {
            'infos': self._failed_infos,
            'extensions': self._failed_extensions
        }

    def get(self, module_name):
        """Return an Extension object for an extension with the given name,
        or None if such a module doesn't exist."""
        return self._extensions.get(module_name, None)

    def inactive_extensions(self):
        return self._inactive_extensions

    def infos(self):
        return self._infos

    def load_settings(self):
        s = QSettings()
        s.beginGroup('extension-settings')
        self._active = s.value('active', True, bool)
        self._inactive_extensions = s.value('installed/inactive', [], list)
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

    def report_failed(self):
        """Show a warning message box if extension(s) could either not
        be loaded or produced errors while parsing the extension infos."""
        from PyQt5.QtWidgets import QMessageBox
        import appinfo

        msg_box = QMessageBox()
        msg_box.setWindowTitle(appinfo.appname)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(_('There were problems loading the extensions.'))
        failed_infos = self._failed_infos
        failed_extensions = self._failed_extensions
        failed_dependencies = self._failed_dependencies
        text = []
        details = []
        if failed_infos:
            text.append(_("  - parsing extension info"))
            details.extend(
                [_('The following extension(s) reported errors with '),
                _('parsing the extension info file:'),
                '',
                '\n'.join(failed_infos.keys())])
        if failed_extensions:
            text.append(_("  - loading extensions"))
            details.extend(
                ['',
                 _('The following extension could not be loaded:'),
                 '',
                 '\n'.join(failed_extensions.keys())])
        if failed_dependencies:
            text.append(_("  - resolving dependencies"))
            text.append(_("    (extensions will not be loaded)"))
            details.extend(
                ['',
                 _('The following problems are reported with dependencies,'),
                 '\n'.join(failed_dependencies)])

        text.extend(
            ['',
            _("More details on the Preferences page")
            ])
        msg_box.setInformativeText('\n'.join(text))
        msg_box.setDetailedText('\n'.join(details))
        msg_box.exec()

    def root_directory(self):
        """Root directory below which extensions are searched for."""
        return self._root_directory

    def set_inactive(self, inactive):
        self._inactive_extensions = inactive

    def set_tools_menu(self, menu):
        """Store a reference to the global Tools menu."""
        self._tools_menu = menu

    def settings_changed(self):
        s = QSettings()
        s.beginGroup('extension-settings')
        active = s.value('active', True, bool)
        inactive = s.value('installed/inactive', [], list)
        root = s.value('root-directory', '', str)
        inactive_changed = False
        if len(inactive) != len(self._inactive_extensions):
            inactive_changed = True
        else:
            for ext in inactive:
                if not ext in self._inactive_extensions:
                    inactive_changed = True
                    break
        self.set_inactive(inactive)
        if (
            active != self.active()
            or root != self.root_directory()
            or inactive_changed
        ):
            from widgets.restartmessage import suggest_restart
            suggest_restart(_('Extensions have changed'))
