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

"""
A simple signal/slot implementation.
"""

import bisect
import contextlib
import types
import weakref


class Signal(object):
    """Use the Signal object at the class definition level:
    
    class MyObject:
    
        somethingChanged = Signal()
        
        def __init__(self):
            pass # etc
    
    def receiver(arg):
        print "Received message:", arg
    
    o = MyObject()
    o.somethingChanged.connect(receiver)
    o.somethingChanged.emit("Hi there")
    
    When the somethingChanged attribute is accessed for the first time through
    an instance, a SignalInstance object is created that provides the signal/
    slot implementation.
    
    """
    
    def __init__(self):
        self.instances = weakref.WeakKeyDictionary()
        
    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            return self.instances[instance]
        except KeyError:
            ret = self.instances[instance] = SignalInstance()


class SignalInstance(object):
    """The SignalInstance object can be used as a signal that receivers (slots)
    can be connected to.
    
    The signal is emitted by the emit() method or by simply invoking it.  Use
    the connect() method to connect functions to it that are called with the
    same arguments as used when emitting the signal.  Currently no argument type
    checking is provided. You can set the priority to influence the order the
    connected slots are called.  The default priority is 0, if you want to have
    a connected slot called before all the others, use e.g. -1, and when you
    want to have a connected slot called after others, use 1 or higher.
    
    If an instance method is connected, the SignalInstance keeps no reference
    to the object the method belongs to. So if the object is garbage collected,
    the signal is automatically disconnected.
    
    If a normal or lambda function is connected, the SignalInstance will keep
    a reference to the function.  If you want to have the function disconnected
    automatically when some object dies, provide that object through the owner
    argument.  Be sure that the connected function does not keep a reference to
    that object though!
    
    You can't connect the same function or method twice, but no exception will
    be raised.
    
    The disconnect() method will disconnect an instance method or function.
    If it wasn't connected no exception is raised.
    
    The clear() method simply disconnects all connected slots.
    
    The blocked() method returns a contextmanager that will block the signals
    as long as it exists:
    
    s = SignalInstance()
    s.connect(receiver)
    with s.blocked():
        doSomething() # code that would cause s to emit a signal
    
    """
    
    def __init__(self):
        self.listeners = []
        self._blocked = False
        
    def connect(self, func, priority=0, owner=None):
        key = makeListener(func, owner)
        if key not in self.listeners:
            key.add(self, priority)
            
    def disconnect(self, func):
        key = makeListener(func)
        try:
            self.listeners.remove(key)
        except ValueError:
            pass
    
    def clear(self):
        del self.listeners[:]
    
    @contextlib.contextmanager
    def blocked(self):
        blocked, self._blocked = self._blocked, True
        try:
            yield
        finally:
            self._blocked = blocked

    def emit(self, *args, **kwargs):
        if not self._blocked:
            for l in self.listeners:
                l.call(args, kwargs)
    
    __call__ = emit


def makeListener(func, owner=None):
    if isinstance(func, types.MethodType):
        return MethodListener(func)
    else:
        return FunctionListener(func, owner)


class ListenerBase(object):
    def __lt__(self, other):
        return self.priority < other.priority
    
    def add(self, signal, priority):
        self.priority = priority
        bisect.insort_right(signal.listeners, self)
        if self.obj is not None:
            def remove(wr, selfref=weakref.ref(self), sigref=weakref.ref(signal)):
                self, signal = selfref(), sigref()
                if self and signal:
                    signal.listeners.remove(self)
            self.obj = weakref.ref(self.obj, remove)
        try:
            nargs = self.func.func_code.co_argcount
        except AttributeError:
            self.argslice = slice(0, None)
        else:
            self.argslice = slice(0, nargs - self.removeargs)


class MethodListener(ListenerBase):
    removeargs = 1
    def __init__(self, meth):
        self.obj = meth.im_self
        self.objid = id(meth.im_self)
        self.func = meth.im_func
            
    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.objid == other.objid and self.func is other.func

    def call(self, args, kwargs):
        obj = self.obj()
        if obj is not None:
            self.func(obj, *args[self.argslice], **kwargs)


class FunctionListener(ListenerBase):
    removeargs = 0
    def __init__(self, func, owner=None):
        self.obj = owner
        self.func = func

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.func is other.func

    def call(self, args, kwargs):
        self.func(*args[self.argslice], **kwargs)
        

