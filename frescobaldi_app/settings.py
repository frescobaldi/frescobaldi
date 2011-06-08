# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Here are simple classes that encapsulate settings for some application parts.

Saving and loading of settings, including defaults, can so be concentrated
in one place.  Because the settings objects are very simple Python classes,
everything (e.g. boundary checking of values, etc.) can be implemented here,
to ensure the application parts get valid settings and defaults.

The classes are intended for single use: just to transfer parameters from
the users configuration files or registry to the application (settings dialog
and also the parts that use the settings), or from the settings dialog to the
configuration files or registry. After that the instance can be thrown away.

The classes should set defaults on init in instance attributes.
They should define a load() class method that returns a new instance with the
loaded settings. They should also have a save() instance method that writes
the settings to the configuration.

"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings


def bound(value, start, end):
    """Clips value so it falls in the int range defined by start and end."""
    return max(start, min(end, value))


class Magnifier(object):
    """Manages settings for the MusicView Magnifier."""
    sizeRange = (200, 800)
    scaleRange = (150, 500)
    
    def __init__(self, size=300, scale=300):
        self.size = size
        self.scale = scale

    @classmethod
    def load(cls):
        """Returns a loaded Magnifier settings instance."""
        self = cls()
        s = QSettings()
        s.beginGroup("musicview/magnifier")
        try:
            self.size = int(s.value("size", self.size))
        except ValueError:
            pass
        try:
            self.scale = int(s.value("scale", self.scale))
        except ValueError:
            pass
        
        self.size = bound(self.size, *cls.sizeRange)
        self.scale = bound(self.scale, *cls.scaleRange)
        return self

    def save(self):
        """Stores the settings."""
        s = QSettings()
        s.beginGroup("musicview/magnifier")
        s.setValue("size", self.size)
        s.setValue("scale", self.scale)


