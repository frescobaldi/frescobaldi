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
Interface for extensions to save and load settings from extension files
"""

import os
import sys

from PyQt6.QtCore import Qt, QObject, QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu

import app

class ExtensionSettings(QObject):
    """
    Manage an extension's settings, serves as an abstraction to QSettings
    to make it easier to handle in an extension and to make it harder
    to create damage.
    Allowed settings and their default values (and implicit types) are defined
    in the Extension class with the _settings_config class variable.
    Extension code should never work with QSettings themselves but interact
    with the extension.settings() object. Settings are loaded once upon startup
    and then maintained in the object. Settings are retrieved thorugh
    settings().get() and changed with settings().set(). When setting a value
    both the settings object is updated and the setting written to disk
    immediately.
    Settings are managed in a 'settings.conf' file in the extension directory.
    """
    def __init__(self, extension):
        super().__init__(extension)
        self._extension = extension
        self._defaults = extension._settings_config
        self._data = dict(self._defaults)
        self._load_settings()

    def extension(self):
        return self._extension

    def get(self, key):
        """Retrieve a setting.
        Raises a KeyError if non-existent key is requested."""
        if not key in self._defaults.keys():
            raise KeyError(
                _("Trying to retrieve unknown setting '{setting}' "
                  "in extension '{extension}'").format(
                    setting=key,
                    extension=self.extension().name()))
        return self._data[key]

    def _load_settings(self):
        """Load settings from disk, is done once upon creation."""
        s = QSettings(self.settings_file(), QSettings.IniFormat)
        for key in self._defaults:
            default = self._defaults[key]
            self._data[key] = s.value(key, default, type(default))

    def set(self, key, value):
        """Set a setting and save it to disk.
        Check type before and raise an exception if necessary."""
        extension_name = (self.extension().display_name()
            or self.extension().name())
        if not key in self._defaults.keys():
            raise KeyError(
                _("Trying to store unknown setting '{setting}' "
                  "in extension '{extension}'").format(
                    setting=key,
                    extension=extension_name))
        try:
            old_value = self._data[key]
            value = type(self._defaults[key])(value)
            if value == old_value:
                return
            self._data[key] = value
            QSettings(self.settings_file(), QSettings.IniFormat).setValue(key, value)
            self.extension().settings_changed(key, old_value, value)
        except ValueError:
            # type conversion failed
            raise ValueError(
                _("Trying to store setting '{setting}' in extension "
                  "'{extension}' with type '{type}' instead of '{type_is}'").format(
                  setting=key,
                  extension=extension_name,
                  type = type(self._defaults[key]),
                  type_is = type(value)))

    def settings_file(self):
        """Return path to 'settings.conf' in the extension directory."""
        extension = self.extension()
        return os.path.join(
            extension.parent().root_directory(),
            extension.name(),
            'settings.conf')
