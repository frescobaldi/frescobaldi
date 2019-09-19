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
import re
from time import perf_counter

from PyQt5.QtCore import (
    QDir,
    QObject,
    QSettings,
    QSize,
    Qt
)
from PyQt5.QtGui import (
    QFont,
    QIcon,
    QStandardItem,
    QStandardItemModel
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QMenu,
    QStyle,
    QTreeView
)

import app
import icons
import vbcl
from . import actions, settings


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
    # - They have to  implement the load_settings() and save_settings() methods.
    # - Instead of a QSettings() object they have to interact with
    #   a self.settings() object that is injected from this class.
    # - Any changes that have to be "applied" (i.e. that should enable
    #   the "Apply" button) must not be saved immediately but emit the
    #   self.parent().changed signal to ensure consistent behaviour
    #   in the Preferences dialog.
    _config_widget_class = None

    # Dictionary of known settings has to be defined in subclasses.
    # Keys are strings - the names of settings.
    # Values are default values to be used, also defining the type, e.g.:
    #   { 'name': 'NN', 'max-entries': 999 }
    _settings_config = {}

    def __init__(self, parent, name):
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
        self._name = name
        self._root_directory = os.path.join(
            parent.root_directory(), self._name)
        self._settings = settings.ExtensionSettings(self)
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
        """Implement to respond to global settings changes
        (e.g. to update GUI or action status).
        This should only respond to changed settings *outside*
        the extension (done in the Preferences dialog). Settings
        changes of the extension itself invoke
        Extension.settings_changed(key, old, new) instead."""
        pass

    def config_widget(self, preference_group):
        """Return a config widget if provided by the extension, or None.
        Do *not* use caching (this is done in the Preferences group),
        set the preference group as the widget's parent,
        inject extension() and settings() attributes."""
        if not self._config_widget_class:
            return None
        widget = self._config_widget_class(preference_group)
        widget.extension = lambda: self
        widget.settings = lambda: self.settings()
        return widget

    def create_panel(self):
        """Create the Extension's Tool Panel if a widget class is provided."""
        if self._panel_widget_class:
            from . import panel
            self._panel = panel.ExtensionPanel(
                self,
                self._panel_widget_class,
                self._panel_dock_area)

    def display_name(self):
        """Return the display name of the extension, or the extension
        key if metadata has not been loaded properly."""
        return self.infos().get('extension-name', self.name())

    def has_icon(self):
        """Returns True if the extension has a custom icon."""
        return self.icon() is not None

    def icon(self):
        """Return the extension's Icon, or None."""
        return self.parent().icon(self.name())

    def infos(self):
        """Return the infos dictionary for the extension,
        or an empty dictionary if they could not be loaded."""
        return self.parent().infos(self.name()) or {}

    def load_time(self):
        """Return the loading time for the Extension object, formatted
        as a string with milliseconds."""
        return self._load_time

    def menu(self, target):
        """Return a submenu for use in an Extensions menu,
        or None if there should be no entry for the given target.
        target may be 'tools' for the main Tools=>Extensions menu,
        or a known keyword for one of the context menus (see
        actions.ExtensionActionCollection.__init__ for the available keys).

        If the target is 'tools' and the extension exports a Panel
        then this will be inserted at the top of the menu, otherwise
        only the action list will be used to create the menu.

        actions.ExtensionActionCollection.set_menu_action_list() is used
        to define the various menu structures that can include 'flat'
        actions and hierarchical submenus.
        """

        def add_action_or_submenu(m, entry):
            if isinstance(entry, QMenu):
                m.addMenu(entry)
            else:
                m.addAction(entry)

        m = self._menus.get(target, None)
        if not m:
            # Menu is not cached already, create it
            actions = self.action_collection().menu_actions(target)
            if target != 'tools' and not actions:
                # empty context menu
                return None
            panel = self.panel()
            # An extension without at least one action or panel is invalid
            if not (panel or actions):
                m = QMenu(_("Invalid extension menu: {}".format(
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
                add_action_or_submenu(m, entry)
        return m

    def name(self):
        """Return the extension's internal name
        (which actually is retrieved from the directory name)."""
        return self._name

    def panel(self):
        """Return the extension's Tool panel, if available, None otherwise."""
        return self._panel

    def root_directory(self):
        """Return the extension's root directory."""
        return self._root_directory

    def set_load_time(self, ms):
        """Store the time needed to load the application.
        A string with two fractional digits in 'ms'."""
        self._load_time = ms

    def settings(self):
        """Reference to the extension's settings object."""
        return self._settings

    def settings_changed(self, key, old, new):
        """Called when a setting *within the extension* has been changed.
        Complements app_settings_changed.
        Can be implemented in subclasses."""
        pass

    def widget(self):
        """Returns the extension's Tool Panel Widget, if available. or None."""
        return self.panel().widget() if self.panel() else None

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


class ExtensionMixin(QObject):
    """Convenience mixin class for widgets in an extension.

    The class provides additional attributes to directly interact with the
    elements of an extension, such as the main Extension object, the settings,
    the mainwindow etc.

    If the 'parent' passed to `__init__(parent)` has an 'extension()' attribute
    (which is for example true when the widget is instantiated as an
    extension's panel widget) this is implicitly made available within the
    widget.
    Otherwise the used class must specify the '_extension_name' class variable,
    exactly using the name matching the extension directory. This is true for
    additional widgets that may be used *within* the panel widget or in newly
    created dialogs etc.
    """

    _extension_name = ''

    def extension(self):
        """Return the actual Extension object if possible."""
        if self._extension_name:
            return app.extensions().get(self._extension_name)
        elif hasattr(self.parent(), 'extension'):
            # The parent has access to the extension (typically the Panel)
            return self.parent().extension()
        else:
            raise AttributeError(_(
                "Class '{classname}' can't access Extension object. "
                "It should provide an _extension_name class variable."
                ).format(classname=self.__class__.__name__))

# More properties are accessed through the extension() property

    def action_collection(self):
        """Return the extension's action collection."""
        return self.extension().action_collection()

    def current_document(self):
        """Return the current document."""
        return self.extension().current_document()

    def mainwindow(self):
        """Return the active MainWindow."""
        return self.extension().mainwindow()

    def panel(self):
        """Return the extension's panel, or None if the widget
        is not a Panel widget and the extension does not have a panel."""
        return self.extension().panel()

    def settings(self):
        """Return the extension's local settings object."""
        return self.extension().settings()


class FailedModel(QStandardItemModel):
    """Data model that is created to report about failed extensions.
    An extension may fail due to errors in the metadata (extension is
    loaded anyway), unresolvable dependencies, or exceptions while
    instantiating the Extension object.

    This data model is created and populated upon program start if
    loading the extension reveals any problems. It is then stored as
    the Extensions object's _failed_model member and reused to populate
    various FailedTree widgets.
    """

    def __init__(self, extensions, data):
        super(FailedModel, self).__init__()
        self.setColumnCount(2)
        self.extensions = extensions
        # Store reference to parent item of failed extensions
        self.exceptions_item = None
        self.populate(data)

    def populate(self, data):
        """Populate the data model using the data passed
        from the extensions object.

        The data model has up to three root-level items:
        - Invalid metadata
        - Failed to load
        - Failed dependencies
        """

        # font for use in various Items
        bold = QFont()
        bold.setWeight(QFont.Bold)

        root = self.invisibleRootItem()
        infos = data['infos']
        if infos:
            # Handle extensions with metadata errors
            infos_item = QStandardItem()
            infos_item.setFont(bold)
            infos_item.setText(_("Invalid metadata:"))
            infos_tooltip = (
                _("Extensions whose extension.cnf file has errors.\n"
                  "They will be loaded nevertheless."))
            infos_item.setToolTip(infos_tooltip)

            root.appendRow(infos_item)
            for info in infos:
                name_item = QStandardItem(info)
                name_item.setToolTip(infos_tooltip)
                icon = self.extensions.icon(info)
                if icon:
                    name_item.setIcon(icon)
                details_item = QStandardItem(infos[info])
                details_item.setToolTip(infos_tooltip)
                infos_item.appendRow([name_item, details_item])

        exceptions = data['exceptions']
        if exceptions:
            # Handle extensions that failed to load properly
            import traceback
            exceptions_item = self.exceptions_item = QStandardItem()
            exceptions_item.setFont(bold)
            exceptions_item.setText(_("Failed to load:"))
            extensions_tooltip = (
                _("Extensions that failed to load properly.\n"
                  "Double click on name to show the stacktrace.\n"
                  "Please contact the extension maintainer."))
            exceptions_item.setToolTip(extensions_tooltip)

            root.appendRow(exceptions_item)
            for ext in exceptions:
                extension_info = self.extensions.infos(ext)
                name = (extension_info.get('extension-name', ext)
                    if extension_info
                    else ext)
                name_item = QStandardItem(name)
                name_item.setToolTip(extensions_tooltip)
                icon = self.extensions.icon(ext)
                if icon:
                    name_item.setIcon(icon)
                exc_info = exceptions[ext]
                # store exception information in the first item
                name_item.exception_info = exc_info
                message = '{}: {}'.format(exc_info[0].__name__, exc_info[1])
                details_item = QStandardItem(message)
                details_item.setToolTip(extensions_tooltip)
                exceptions_item.appendRow([name_item, details_item])

        dependencies = data['dependencies']
        if dependencies:
            # Handle extensions with dependency issues
            dep_item = QStandardItem(_("Failed dependencies:"))
            dep_item.setFont(bold)
            dep_tooltip = (
                _("Extensions with failed or circular dependencies.\n"
                  "They are not loaded."))
            dep_item.setToolTip(dep_tooltip)

            root.appendRow(dep_item)
            missing = dependencies.get('missing', None)
            if missing:
                missing_item = QStandardItem(_("Missing:"))
                missing_item.setFont(bold)
                missing_item.setToolTip(dep_tooltip)
                dep_item.appendRow(missing_item)
                for m in missing:
                    item = QStandardItem(m)
                    item.setToolTip(dep_item)
                    missing_item.appendRow(item)
            inactive = dependencies.get('inactive', None)
            if inactive:
                inactive_item = QStandardItem(_("Inactive:"))
                inactive_item.setFont(bold)
                inactive_item.setToolTip(dep_tooltip)
                dep_item.appendRow(inactive_item)
                for i in inactive:
                    item = QStandardItem(i)
                    item.setToolTip(dep_tooltip)
                    inactive_item.appendRow(item)
            circular = dependencies.get('circular', None)
            if circular:
                circular_item = QStandardItem(_("Circular:"))
                circular_item.setFont(bold)
                circular_item.setToolTip(dep_tooltip)
                dep_item.appendRow(circular_item)
                item = QStandardItem(' | '.join(circular))
                item.setToolTip(dep_tooltip)
                circular_item.appendRow(item)


class FailedTree(QTreeView):
    """QTreeView descendant to display information about failed extensions
    in the initial message dialog and the Preferences panel.
    The strategy is to create the QTreeView object everytime it is used
    without having to re-populate the data model."""

    # QStandardItemModel is set when any failed extensions are detected
    # while loading extensions. So checking for this class variable can
    # determine whether any extensions failed
    _model = None

    def __init__(self, parent=None):
        super(FailedTree, self).__init__(parent)
        #TODO: Set the height of the QTreeView to 4-6 rows
        #https://stackoverflow.com/questions/53591159/set-the-height-of-a-qtreeview-to-height-of-n-rows
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setHeaderHidden(True)
        self.setModel(self._model)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.doubleClicked.connect(self.tree_double_clicked)

    def tree_double_clicked(self, index):
        """Show the details of a failed extension in a message box."""
        model = self.model()
        item = model.itemFromIndex(index)
        parent = item.parent()
        if item and item.parent() == model.exceptions_item:

            # TODO: Change this to the Exception handling message box
            # (with option to write an email to maintainer)

            import traceback
            from PyQt5.QtWidgets import QMessageBox
            import appinfo
            row = item.row()
            name_item = parent.child(row, 0)
            message_item = parent.child(row, 1)
            msg_box = QMessageBox()
            msg_box.setWindowTitle(_(appinfo.appname))
            msg_box.setIcon(QMessageBox.Information)
            extension_name = name_item.text()
            exception_info = name_item.exception_info
            msg_box.setText(
                _("Extension '{}' failed to load with the given "
                  "explanation\n\n{}").format(
                    extension_name, message_item.text()))
            msg_box.setInformativeText(
                ' '.join(traceback.format_exception(*exception_info)))
            msg_box.exec()


class Extensions(QObject):
    """Global object managing the extensions.
    Accessed with app.extensions()"""

    def __init__(self, mainwindow):
        super(Extensions, self).__init__()
        self._mainwindow = mainwindow
        # Resources are handled on the global Extensions level because
        # in a number of cases they are independent from an actually
        # loaded Extension object (i.e. have to be functional before loading
        # or with failed extensions too)
        self._menus = {}
        self._icons = {}
        self._infos = {}
        self._extensions = {}
        self._extensions_ordered = []
        self._failed_infos = {}
        self._failed_dependencies = []
        self._failed_extensions = {}

        # These will be set in load_settings():
        self._root_directory = None
        self._active = False
        self._inactive_extensions = []
        self.load_settings()
        app.settingsChanged.connect(self.settings_changed)

        # Only process extensions if root directory is configured properly
        if not (self.root_directory()
            and os.path.isdir(self.root_directory())):
            return
        # Info about *installed* extensions is loaded
        # regardless of 'active' state
        self.load_infos()
        if self.active():
            self._extensions_ordered = self.check_dependencies()
            #if not self._failed_dependencies:
            self.load_extensions()
            if (self._failed_infos
                or self._failed_extensions
                or self._failed_dependencies):
                FailedTree._model = FailedModel(self, {
                    'infos': self._failed_infos,
                    'dependencies': self._failed_dependencies,
                    'exceptions': self._failed_extensions
                })
                self.report_failed()
        del self._failed_infos
        del self._failed_dependencies
        del self._failed_extensions

    def active(self):
        """Returns True if extensions are enabled globally."""
        return self._active

    def check_dependencies(self):
        """Check extension metadata for unresolved or circular dependencies.

        Returns a list of extension keys in topological order.
        Inactive extensions are skipped.
        Extensions with missing dependencies are logged and skipped.
        Circular dependencies are looged and skipped.
        """

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
        # https://en.wikipedia.org/wiki/Topological_sorting#Algorithms
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
                # missing and inactive dependencies are beside Kahn's algorithm
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
            self._failed_dependencies = {}
            message = []
            if missing_dependencies:
                missing = self._failed_dependencies['missing'] = []
                for dep in missing_dependencies:
                    ext = dep[0]
                    if ext in result:
                        result.remove(ext)
                    missing.append("{} => {}".format(ext, dep[1]))
            if inactive_dependencies:
                inactive = self._failed_dependencies['inactive'] = []
                for dep in inactive_dependencies:
                    ext = dep[0]
                    if ext in result:
                        result.remove(ext)
                    inactive.append("{} => {}".format(ext, dep[1]))
            if incoming:
                # If there remain incoming edges we have a
                # circular depencency (according to Kahn's algorithm)
                self._failed_dependencies['circular'] = [
                    ext for ext in incoming.keys()]
        # List of extensions with all dependencies resolved,
        # and ordered in correct topological order
        return reversed(result)

    def load_extensions(self):
        """Load active extensions in topological order."""
        root = self.root_directory()
        if not root in sys.path:
            sys.path.append(root)

        for ext in [ext for ext  in self._extensions_ordered
            if not ext in self.inactive_extensions()]:
            try:
                # measure loading time
                start = perf_counter()
                # Try importing the module. Will fail here if there's
                # no Python module in the subdirectory or loading the module
                # produces errors
                module = importlib.import_module(ext)
                # Add extension's icons dir (if present) to icon search path
                icon_path = os.path.join(self.root_directory(), ext, 'icons')
                if os.path.isdir(icon_path):
                    search_paths = QDir.searchPaths('icons')
                    QDir.setSearchPaths('icons', [icon_path] + search_paths)
                # Instantiate the extension,
                # this will fail if the module is no valid extension
                # (doesn't have an Extension class) or has other errors in it
                extension = module.Extension(self, ext)
                end = perf_counter()
                extension.set_load_time(
                    "{:.2f} ms".format((end - start) * 1000))
                self._extensions[ext] = extension
            except Exception as e:
                self._failed_extensions[ext] = sys.exc_info()

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
        if icon == False: # None would be a valid result indicating 'no icon'
            self._load_icon(name)
        return self._icons[name]

    def _load_infos(self, extension_name):
        """Load an extension's metadata from the extension.cnf file.
        Optional keys are assigned 'empty' default values, while
        missing mandatory keys will cause the load to fail. Such extensions
        will be reported as "Failed metadata", but the extension is
        loaded anyway."""

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
            return None

    def load_infos(self):
        """Load extension metadata from all subdirs that include an
        extension.cnf file."""
        root = self.root_directory()
        subdirs = [dir for dir in os.listdir(root) if os.path.isfile(
            os.path.join(root, dir, 'extension.cnf'))]
        for d in subdirs:
            self._infos[d] = self._load_infos(d)

    def extensions(self):
        """Return a list of all loaded extensions, ordered by their
        display name."""
        result = [self._extensions[ext] for ext in self._extensions.keys()]
        result.sort(key=lambda extension: extension.display_name())
        return result

    def get(self, name):
        """Return an Extension object for an extension with the given name,
        or None if such a module doesn't exist."""
        return self._extensions.get(name, None)

    def inactive_extensions(self):
        """Return a list with names of extensions marked as inactive."""
        return self._inactive_extensions

    def infos(self, name):
        return self._infos.get(name, None)

    def installed_extensions(self):
        """Return a list of all installed extensions, independently of their
        load status."""
        result = list(self._infos.keys())
        return sorted(result)

    def is_extension_exception(self, traceback):
        """Check if the given traceback points to an exception occuring
        within an extension. If so, return a tuple with
        - extension name (display name)
        - first maintainer
        - extension key.
        If the exception is *not* from an extension return None"""
        regex = re.compile(
            '\s*File \"({root}){sep}(.*)\"'.format(
            sep=os.sep,
            root=self.root_directory()))
        for line in traceback:
            m = regex.match(line)
            if m:
                tail = m.groups()[1]
                m = re.match('(.*){sep}.*'.format(sep=os.sep), tail)
                extension = m.groups()[0]
                infos = self.infos(extension)
                if infos:
                    return (infos['extension-name'],
                            infos['maintainers'][0],
                            extension)

    def load_settings(self):
        """Load application-wide settings relating to extensions."""
        s = QSettings()
        s.beginGroup('extension-settings')
        self._active = s.value('active', True, bool)
        self._inactive_extensions = s.value('installed/inactive', [], str)
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

        from PyQt5.QtCore import QCoreApplication
        import appinfo
        import qutil
        import widgets.dialog

        dlg = widgets.dialog.Dialog(
            self.mainwindow(),
            icon='warning',
            buttons=('ok',),
            title=appinfo.appname,
            message=_(
                "There were problems loading the extensions.\n"
                "The following details are also available from the "
                "Preferences dialog."))
        dlg.setMainWidget(FailedTree(self.mainwindow()))
        qutil.saveDialogSize(
            dlg, "extensions/error-dialog/size", QSize(600, 300))
        dlg.setGeometry(QStyle.alignedRect(
            Qt.RightToLeft,
            Qt.AlignCenter,
            dlg.size(),
            app.qApp.desktop().availableGeometry()))
        dlg.exec()

    def reset_inactive(self, inactive):
        """Save the list of inactive extensions."""
        self._inactive_extensions = list(inactive)

    def root_directory(self):
        """Root directory below which extensions are searched for."""
        return self._root_directory

    def set_inactive(self, extension, state=True):
        """Set one extension to active/inactive"""
        if state:
            if not extension in self._inactive_extensions:
                self._inactive_extensions.append(extension)
        else:
            if extension in self._inactive_extensions:
                self._inactive_extensions.remove(extension)

    def set_tools_menu(self, menu):
        """Store a reference to the global Tools menu."""
        self._tools_menu = menu

    def settings_changed(self):
        """Determine if any changes in global extension settings
        requires a restart."""
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
        self.reset_inactive(inactive)
        if (
            active != self.active()
            or root != self.root_directory()
            or inactive_changed
        ):
            from widgets.restartmessage import suggest_restart
            suggest_restart(_('Extensions have changed'))
