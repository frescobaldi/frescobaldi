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
Extensions preferences.
"""


from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTreeView,
    QVBoxLayout,
    QWidget
)

import app
import appinfo
import preferences
from widgets import urlrequester
from extensions import FailedTree

class Extensions(preferences.ScrolledGroupsPage):
    """Extensions page for Preferences"""

    def __init__(self, dialog):
        super(Extensions, self).__init__(dialog)

        self._active = QSettings().value(
            'extension-settingss/active', True, bool)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(General(self))
        layout.addWidget(Installed(self))
        if FailedTree._model:
            layout.addWidget(Failed(self))
        layout.addWidget(Config(self))
        layout.addStretch(1)

    def active(self):
        return self._active


class General(preferences.Group):
    """Application-wide settings for extensions."""

    def __init__(self, page):
        super(General, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        header_layout = QHBoxLayout()
        self.active = QCheckBox(toggled=self.changed)
        header_layout.addWidget(self.active)

        self.api_version = QLabel()
        header_layout.addStretch()
        header_layout.addWidget(self.api_version)

        layout.addLayout(header_layout)

        self.root = urlrequester.UrlRequester()
        self.root.changed.connect(self.changed)
        layout.addWidget(self.root)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("General Settings"))
        self.active.setText(_("Use Extensions"))
        self.api_version.setText(_("Extension API: {apiversion}").format(
            apiversion=appinfo.extension_api))
        self.active.setToolTip(_("If unchecked don't look for extensions."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("extension-settings")
        self.active.setChecked(s.value("active", True, bool))
        self.root.setPath(s.value("root-directory", '', str))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("extension-settings")
        s.setValue("active", self.active.isChecked())
        s.setValue("root-directory", self.root.path())

    def root_changed(self):
        self.changed.emit()


class Installed(preferences.Group):
    """Overview of installed extensions.

    A QTreeView lists the metadata of all installed extensions.
    If the currently selected extension provides a configuration
    widget it is displayed in the bottom group of the page.

    With a checkbox individual extensions can be deactivated.
    Metadata is listed for all *installed* extensions, regardless
    of manual deactivation or load failure.
    """

    def __init__(self, page):
        super(Installed, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # This must be called before self.populate() because
        # the data model relies on the labels
        app.translateUI(self)

        self.tree = QTreeView()
        self.name_items = {}
        self._selected_extension = ''
        self.tree.setModel(QStandardItemModel())
        self.tree.model().setColumnCount(2)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setHeaderHidden(True)
        self.tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.tree.selectionModel().selectionChanged.connect(
            self.selection_changed)
        self.populate()
        layout.addWidget(self.tree)

    def translateUI(self):
        self.setTitle(_("Installed Extensions"))
        self.config_labels = {
            'extension-name': _("Name"),
            'maintainers': _("Maintainer(s)"),
            'version': _("Version"),
            'api-version': _("API version"),
            'license': _("License"),
            'short-description': _("Short Description"),
            'description': _("Description"),
            'repository': _("Repository"),
            'website': _("Website"),
            'dependencies': _("Dependencies")
        }

    def loadSettings(self):
        s = QSettings()
        self.setEnabled(self.page().active())
        s.beginGroup("extension-settings/installed")
        inactive = s.value("inactive", [], list)
        for ext in self.name_items.keys():
            self.name_items[ext].setCheckState(
                Qt.Checked if ext not in inactive else Qt.Unchecked)
        self.tree.model().dataChanged.connect(self.page().changed)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("extension-settings/installed")
        inactive = [ext for ext in self.name_items.keys()
            if self.name_items[ext].checkState() == Qt.Unchecked]
        s.setValue("inactive", inactive)

    def populate(self):
        """Populate the tree view with data from the installed extensions.
        """

        # TODO/Question:
        # Would it make sense to move this to a dedicated model class
        # complementing the FailedModel?

        root = self.tree.model().invisibleRootItem()
        extensions = app.extensions()
        for ext in extensions.installed_extensions():
            ext_infos = extensions.infos(ext)
            display_name = ext_infos.get(ext, ext) if ext_infos else ext.name()
            loaded_extension = extensions.get(ext)
            if loaded_extension:
                display_name += ' ({})'.format(loaded_extension.load_time())

            name_item = QStandardItem(display_name)
            name_item.extension_name = ext
            name_item.setCheckable(True)
            self.name_items[ext] = name_item
            icon = extensions.icon(ext)
            if icon:
                name_item.setIcon(icon)
            root.appendRow([name_item])
            for entry in [
                'extension-name',
                'short-description',
                'description',
                'version',
                'api-version',
                'dependencies',
                'maintainers',
                'repository',
                'website',
                'license'
            ]:
                label_item = QStandardItem('{}:'.format(
                    self.config_labels[entry]))
                label_item.setTextAlignment(Qt.AlignTop)
                bold = QFont()
                bold.setWeight(QFont.Bold)
                label_item.setFont(bold)
                details = ext_infos.get(entry, "") if ext_infos else ""
                if type(details) == list:
                    details = '\n'.join(details)
                details_item = QStandardItem(details)
                details_item.setTextAlignment(Qt.AlignTop)
                if entry == 'api-version':
                    # Check for correct(ly formatted) api-version entry
                    # and highlight it in case of mismatch
                    api_version = appinfo.extension_api
                    if not details:
                        details_item.setFont(bold)
                        details_item.setText(
                            _("Misformat: {api}").format(details))
                    elif not details == api_version:
                            details_item.setFont(bold)
                            details_item.setText('{} ({}: {})'.format(
                                details,
                                appinfo.appname,
                                api_version))
                name_item.appendRow([label_item, details_item])

    def selected_extension(self):
        """Return the (directory) name of the extension that
        is currently selected."""
        return self._selected_extension

    def selection_changed(self, new, old):
        """Show the configuration widget for the selected extension,
        if available."""
        config = self.siblingGroup(Config)
        if new.indexes():
            ext_item = self.tree.model().itemFromIndex(new.indexes()[0])
            # NOTE: This may have to be changed if there should be
            # more complexity in the tree model than now (a selected
            # row is either a top-level row or its immediate child)
            if not hasattr(ext_item, 'extension_name'):
                ext_item = ext_item.parent()
            name = ext_item.extension_name
            if name == self.selected_extension():
                return
        else:
            # If nothing is selected, show the "empty" widget
            name = ""

        config.hide_extension()
        self._selected_extension = name
        config.show_extension(name)


class Failed(preferences.Group):
    """Show information about extensions that failed to load properly.
    This is only instantiated if there *are* failed extensions."""

    def __init__(self, page):
        super(Failed, self).__init__(page)
        import extensions
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.tree = extensions.FailedTree(self)
        layout.addWidget(self.tree)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Failed Extensions"))


class Config(preferences.Group):
    """Configuration of an extension.
    If the currently selected extension doesn't provide a
    config widget this will show a dummy widget instead."""

    def __init__(self, page):
        super(Config, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._widgets = {}
        # Create an "empty" widget as a placeholder for
        # extensions that don't provide a config widget
        self.empty_widget = QWidget(self)
        empty_layout = QVBoxLayout()
        self.empty_widget.setLayout(empty_layout)
        self.empty_label = QLabel(self)
        empty_layout.addWidget(self.empty_label)
        layout.addWidget(self.empty_widget)

        # Reference to the current widget, initialize to empty widget
        self.current_widget = self.empty_widget
        self.current_widget.hide()

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Extension Configuration"))
        self.empty_label.setText(_(
            "The selected extension does not "
            "provide a configuration widget "
            "or is inactive."))

    def loadSettings(self):
        """Load global settings. Any ConfigWidget class must implement
        save_settings(), but this is called right after instantiating
        the widget in self.widget()."""
        self.setEnabled(self.page().active())

    def saveSettings(self):
        """Ask all extension configuration widgets to save their settings.
        Configuration widgets are required to implement save_settings()."""
        for widget in self._widgets.values():
            if widget:
                widget.save_settings()

    def hide_extension(self):
        """Remove the currently displayed configuration widget."""
        self.layout().removeWidget(self.current_widget)
        self.current_widget.hide()
        self.current_widget = None

    def show_extension(self, name):
        """Show an extension's configuration widget, or the
        empty widget if the extension does not provide one."""
        #widget = self._widgets.get(name, self.empty_widget)
        widget = self.widget(name) or self.empty_widget
        self.current_widget = widget
        self.layout().addWidget(widget)
        widget.show()

    def widget(self, extension):
        """Return a configuration widget if provided by the extension,
        or None otherwise."""
        widget = self._widgets.get(extension, False)
        if widget == False:
            ext = app.extensions().get(extension)
            # skip non-loaded extensions
            if ext:
                widget = ext.config_widget(self)
                widget.load_settings()
            self._widgets[extension] = widget or None
        return widget
