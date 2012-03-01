# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2012 by Wilbert Berendsen
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
An advanced property that computes and caches expensive operations
(such as running an external command and reading its output).

A callback when a value is computed/read is also supported.

You may inherit from CachedProperty to implement the logic to compute
or retrieve the value, or you my initialize the CachedProperty with a function
that runs in the context of the CachedProperty, which is called in the context
of the property.

If you are using the property as a descriptor e.g.:

import cachedproperty

class MyClass(object):
    version = cachedproperty.cachedproperty()

obj = MyClass()

you can retrieve the value with

    obj.version()

you can force the value to be computed with

    obj.version.start()

(and be notified when set with:

    obj.version.computed.connect(myfunction)

), and delete the value with

    del obj.version

If you want the value now or later, you can also use

    obj.version.callback(myfunction)

which will call myfunction either now or later with the value.

Properties can also depend on each other:

class MyClass(object):

    @cachedproperty.cachedproperty
    def command(self):
        # ....
    
    @cachedproperty.cachedproperty(depends=command)
    def version(self):
        cmd = self.instance().command
        # command has already been computed when this function runs.


This module uses the signals module for the callback logic.

"""

from __future__ import unicode_literals

import weakref

import signals


class CachedProperty(object):    
    """An advanced property that can compute and cache expensive operations.
    
    This can be used to e.g. run an external command and read its output.

    A callback when a value is computed/read is also supported, either via
    the callback() method or the computed() signal.
    
    """
    
    # emitted when the value for the property is computed.
    # the value is given as argument.
    computed = signals.Signal()
    
    @classmethod
    def cachedproperty(cls, func=None, depends=None):
        """Decorator to make cached properties."""
        if func is not None:
            return cls(func, depends=depends)
        elif depends is None:
            return cls
        def decorator(func):
            return cls(func, depends=depends)
        return decorator
    
    def __init__(self, func=None, instance=None, depends=None):
        self._value = None
        self._running = False
        self._func = func
        if instance:
            self._instance = weakref.ref(instance)
        else:
            self._instance = lambda: None
        if depends is None:
            self._depends = ()
        elif not isinstance(depends, (tuple, list)):
            self._depends = (depends,)
        else:
            self._depends = depends
            
    # descriptor part
    def __get__(self, instance, cls=None):
        if instance is None:
            return self._func or self
        try:
            return instance.__cachedproperties[self]
        except AttributeError:
            instance.__cachedproperties = {}
        except KeyError:
            pass
        ret = type(self)(self._func, instance, depends=self._depends)
        instance.__cachedproperties[self] = ret
        return ret
    
    def __set__(self, instance, value):
        self.__get__(instance).set(value)
    
    def __delete__(self, instance):
        self.__get__(instance).unset()
    
    # property part
    def instance(self):
        """Returns the instance we are a property for."""
        return self._instance()
        
    def set(self, value):
        """Sets a value.
        
        If the value is not None, the computed(value) signal is emitted.
        
        """
        self._value = value
        self._running = False
        if value is not None:
            self.computed.emit(value)
            self.computed.clear()
        
    def unset(self):
        """Sets the value to None, the property is considered unset."""
        self._value = None
    
    def get(self):
        """Retrieves the value, which may be None (unset)."""
        return self._value
    
    __call__ = get
    
    def callback(self, func):
        """Calls the specified function back with the value.
        
        If the value already is known, the callback is performed immediately
        (synchronuous) and this method returns True.
        
        If the value yet has to be computed, the function is connected to the
        computed() signal and start() is called, so the function is called later
        with the value. In that case this method returns None.
        
        """
        if self._value is not None:
            func(self._value)
            return True
        self.computed.connect(func)
        self.start()
    
    def start(self):
        """Starts the machinery that computes the value.
        
        This simply happens by calling run(), which should be reimplemented
        to perform the actual action.
        
        """
        if not self._running:
            self._running = True
            self.checkstart()
    
    def checkstart(self):
        """Starts if all dependencies are met."""
        for d in self._depends:
            prop = d.__get__(self.instance())
            if prop.get() is None:
                prop.computed.connect(self.checkstart)
                prop.start()
                break
        else:
            self.run()
    
    def run(self):
        """Implement this method to start the computation.
        
        The result must be set using self.set(value), which will automatically
        call all registered callbacks once.
        
        The default implementation starts the function, if given on init.
        
        """
        if self._func:
            instance = self.instance()
            if instance:
                result = self._func(instance)
                if result is not None:
                    self.set(result)
        else:
            self.set("(null)")


cachedproperty = CachedProperty.cachedproperty

