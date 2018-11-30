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


import re

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel

from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFontComboBox,
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
    QTreeView, QVBoxLayout, QWidget
)

import app
import userguide
import qutil
import preferences
import popplerview
import widgets.dialog
import widgets.listedit
import documentstructure
from widgets import urlrequester


class Extensions(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(Extensions, self).__init__(dialog)

        self._active = QSettings().value(
            'extension-settingss/active', True, bool)

        self._extensions = app.extensions().extensions() if self._active else None

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(General(self))
        layout.addWidget(Installed(self))
        layout.addWidget(Config(self))
        layout.addStretch(1)

    def active(self):
        return self._active

    def extensions(self):
        return self._extensions


class General(preferences.Group):
    def __init__(self, page):
        super(General, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.active = QCheckBox(toggled=self.changed)
        layout.addWidget(self.active)

        self.root = urlrequester.UrlRequester()
        self.root.changed.connect(self.root_changed)
        layout.addWidget(self.root)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("General Settings"))
        self.active.setText(_("Use Extensions"))
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

    At some later point the entries in the tree view will
    show more information about the extensions (provided metadata),
    and there should be widgets (a checkbox?) to de/activate individual
    extensions.
    When the currently selected extension provides a configuration widget
    this will be shown in the third Group element (to-be-done).
    """
    def __init__(self, page):
        super(Installed, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tree = QTreeView()
        if page.active():
            self.tree.setModel(QStandardItemModel())
            # We don't completely remove the headers because they will
            # be used later.
            self.tree.model().setHorizontalHeaderLabels([''])
            self.tree.selectionModel().selectionChanged.connect(
                self.selection_changed)
            self.populate()
        layout.addWidget(self.tree)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Installed Extensions"))

    def loadSettings(self):
        s = QSettings()
        self.setEnabled(self.page().active())
        s.beginGroup("extension-settings/installed")
        # to be continued if there should be anything to be stored here

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("extension-settings/installed")
        # to be continued if there should be anything to be stored here

    def populate(self):
        """Populate the tree view with data from the installed extensions.
        """
        # For now we'll create a flat list but there will be child items
        # with further metadata and configuration interface later.
        root = self.tree.model().invisibleRootItem()
        for ext in self.page().extensions():
            item = QStandardItem(ext.display_name())
            item.extension_name = ext.name()
            if ext.has_icon():
                item.setIcon(ext.icon())
            root.appendRow(item)

    def selection_changed(self, new, old):
        """Show the configuration widget for the selected extension,
        if available."""
        config = self.siblingGroup(Config)
        config.hide_extension()
        if new.indexes():
            # NOTE: The following approach may have to be modified
            # when there will be more than one column in the model
            ext_item = self.tree.model().itemFromIndex(new.indexes()[0])
            name = ext_item.extension_name
        else:
            # If nothing is selected, show the "empty" widget
            name = ""

        config.show_extension(name)


class Config(preferences.Group):
    """Configuration of an extension.
    If the currently selected extension doesn't provide a
    config widget this will show a dummy widget instead."""

    def __init__(self, page):
        super(Config, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

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

        if page.active():
            # preload and reference config widgets for all extensions
            self.config_widgets = {}
            for ext in page.extensions():
                widget = ext.config_widget(self)
                if widget:
                    widget.hide()
                    self.config_widgets[ext.name()] = widget

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Extension Configuration"))
        self.empty_label.setText(_(
            "The selected extension does not\n"
            "provide a configuration widget."))

    def loadSettings(self):
        """Ask all extension configuration widgets to load their settings.
        Configuration widgets are required to implement load_settings()."""
        self.setEnabled(self.page().active())
        for widget in self.config_widgets.values():
            widget.load_settings()

    def saveSettings(self):
        """Ask all extension configuration widgets to save their settings.
        Configuration widgets are required to implement save_settings()."""
        for widget in self.config_widgets.values():
            widget.save_settings()

    def hide_extension(self):
        """Remove the currently displayed configuration widget."""
        self.layout().removeWidget(self.current_widget)
        self.current_widget.hide()
        self.current_widget = None

    def show_extension(self, name):
        """Show an extension's configuration widget, or the
        empty widget if the extension does not provide one."""
        widget = self.config_widgets.get(name, self.empty_widget)
        self.current_widget = widget
        self.layout().addWidget(widget)
        widget.show()
