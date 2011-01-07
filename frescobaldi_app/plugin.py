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
Simple internal plugin api.
"""

import weakref

_instances = weakref.WeakKeyDictionary()


class Plugin(object):
    @classmethod
    def instance(cls, obj):
        """Returns the instance of this plugin type for this object.
        
        The plugin instance is created if it did not exist.
        
        """
        try:
            return _instances[cls][obj]
        except KeyError:
            instances = _instances.setdefault(cls, weakref.WeakKeyDictionary())
            result = instances[obj] = object.__new__(cls, obj)
            result._parent = weakref.ref(obj)
            result.__init__(obj)
        return result
    
    @classmethod
    def instances(cls):
        """Iterates over all living instances of this plugin."""
        try:
            for instance in _instances[cls].items():
                yield instance
        except KeyError:
            pass


class DocumentPlugin(Plugin):
    def document(self):
        return self._parent()


class MainWindowPlugin(Plugin):
    def mainwindow(self):
        return self._parent()


