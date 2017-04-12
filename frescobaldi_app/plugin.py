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
Simple internal plugin api.

A Plugin is like an extension of the object it is used for. You would
normally subclass it to do useful things. It is created by calling the
instance(obj) method and lives as long as the object lives. When calling
instance(obj) again, the same Plugin instance is returned.

The Plugin instance keeps a weak reference to its object in the _parent
attribute. The object is unchanged, it knows nothing about the plugin.

There are three often used Plugin classes defined here:
MainWindowPlugin (for MainWindow instances), DocumentPlugin (for Document instances)
and ViewSpacePlugin (for ViewSpace instances).

Also the Attributes class is defined here, which is a simple class without methods
but with special instance attribute handling:
- when setting attributes on an instance, weak references are used when possible
- when requesting non-existing attributes, None is returned
- deleting an attribute does not fail if it doesn't exist.

You can use this class to store information to associate objects with each other,
but without keeping references to them.

Finally there is an AttributePlugin class, combining the Attributes and Plugin classes.

"""


import weakref

_instances = weakref.WeakKeyDictionary()


class Plugin(object):
    """Base class for plugins.

    A Plugin is coupled to another object and is automatically garbage collected
    as soon as the other object disappears.

    Use the instance() class method to get/create the Plugin instance for an object.

    Implement the __init__() method if you want to do some setup.

    The instances() class method returns all living instances of this plugin type.

    """
    def __init__(self, obj):
        """Implement this method to setup the plugin instance."""
        pass

    @classmethod
    def instance(cls, obj):
        """Returns the instance of this plugin type for this object.

        The plugin instance is created if it did not exist.

        """
        try:
            return _instances[cls][obj]
        except KeyError:
            instances = _instances.setdefault(cls, weakref.WeakKeyDictionary())
            result = instances[obj] = cls.__new__(cls, obj)
            result._parent = weakref.ref(obj)
            result.__init__(obj)
        return result

    @classmethod
    def instances(cls):
        """Iterates over all living instances of this plugin."""
        try:
            return _instances[cls].values()
        except KeyError:
            return ()


class Attributes(object):
    """Manages attributes.

    The attributes can be set simply as instance attributes.

    If an attribute is set, it is stored as a weak reference when possible
    If an attribute is requested but not set or its value does not exist anymore,
    None is returned.
    Deleting an attribute does not fail if it doesn't exist.

    """
    def __init__(self):
        self._attrs = {}

    def __getattr__(self, name):
        val = self._attrs.get(name)
        if isinstance(val, weakref.ref):
            return val()
        else:
            return val

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            try:
                value = weakref.ref(value)
            except TypeError:
                pass
            self._attrs[name] = value

    def __delattr__(self, name):
        try:
            del self._attrs[name]
        except KeyError:
            pass


class AttributePlugin(Plugin, Attributes):
    """Base class for a Plugin managing attributes for any object."""
    def __init__(self, obj):
        """Implement this method to setup the plugin instance.

        For this class (AttributePlugin) you must also call this constructor if you reimplement it.

        """
        Attributes.__init__(self)


class DocumentPlugin(Plugin):
    """Base class for plugins that live besides a Document."""
    def document(self):
        """Returns the Document this plugin is used for."""
        return self._parent()


class MainWindowPlugin(Plugin):
    """Base class for plugins that live besides a MainWindow."""
    def mainwindow(self):
        """Returns the MainWindow this plugin is used for."""
        return self._parent()


class ViewSpacePlugin(Plugin):
    """Base class for plugins that live besides a ViewSpace."""
    def viewSpace(self):
        """Returns the ViewSpace this plugin is used for."""
        return self._parent()


class ViewPlugin(Plugin):
    """Base class for plugins that live besides a View."""
    def view(self):
        """Returns the View this plugin is used for."""
        return self._parent()


