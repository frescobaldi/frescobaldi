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
Simple internal plugin api.
"""

from __future__ import unicode_literals

import weakref

_instances = weakref.WeakKeyDictionary()


class Plugin(object):
    """Base class for plugins.
    
    A Plugin is coupled to another object and is automatically garbage collected
    as soon as the other object disappears.
    
    Use the instance() class method to get/create one for an object.
    
    Implement the __init__() method if you want to do some setup.
    This method then needs to accept the arguments you give to the instance()
    class method.
    
    The instances() class method returns all living instances of this plugin type.
    
    """
    def __init__(self, *args, **kwargs):
        pass
    
    @classmethod
    def instance(cls, obj, *args, **kwargs):
        """Returns the instance of this plugin type for this object.
        
        The plugin instance is created if it did not exist.
        
        """
        try:
            return _instances[cls][obj]
        except KeyError:
            instances = _instances.setdefault(cls, weakref.WeakKeyDictionary())
            result = instances[obj] = cls.__new__(cls, obj, *args, **kwargs)
            result._parent = weakref.ref(obj)
            result.__init__(obj, *args, **kwargs)
        return result
    
    @classmethod
    def instances(cls):
        """Iterates over all living instances of this plugin."""
        try:
            return _instances[cls].values()
        except KeyError:
            return ()


class DocumentPlugin(Plugin):
    """Base class for plugins that live besides a Document."""
    def document(self):
        return self._parent()


class MainWindowPlugin(Plugin):
    """Base class for plugins that live besides a MainWindow."""
    def mainwindow(self):
        return self._parent()


class ViewSpacePlugin(Plugin):
    """Base class for plugins that live besides a ViewSpace."""
    def viewSpace(self):
        return self._parent()


