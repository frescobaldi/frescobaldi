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
A simple signal/slot implementation.

Functions or methods can be connected to Signal instances, and when the
Signal instance is called (or its emit() method is called, which is equivalent),
all connected methods or function are automatically called.

When a Signal is created as a class attribute and accessed via an instance of
that class, it creates a Signal instance specifically for that object.

When methods are connected, no reference is kept to the method's object. When
the object is garbage collected, the signal is automatically disconnected.

A special Signal variation is also available, the SignalContext. Methods or
functions connected to this signal should return context managers which are
entered when the signal is entered in a context (with) block.

"""

import bisect
import contextlib
import types
import weakref
import sys


__all__ = ["Signal", "SignalContext"]


class Signal(object):
    """A Signal can be emitted and receivers (slots) can be connected to it.

    An example:

    class MyObject(object):

        somethingChanged = Signal()

        def __init__(self):
            pass # etc

        def doSomething(self):
            ... do things ...
            self.somethingChanged("Hi there!")     # emit the signal

    def receiver(arg):
        print("Received message:", arg)


    >>> o = MyObject()
    >>> o.somethingChanged.connect(receiver)
    >>> o.doSomething()
    Received message: Hi there!

    A Signal() can be used directly or as a class attribute, but can also be
    accessed as an attribute of an instance, in which case it creates a Signal
    instance for that instance.

    The signal is emitted by the emit() method or by simply invoking it.

    It is currently not possible to enforce argument types that should be used
    when emitting the signal. But if called methods or functions expect fewer
    arguments than were given on emit(), the superfluous arguments are left out.

    Methods or functions are connected using connect() and disconnected using
    disconnect(). It is no problem to call connect() or disconnect() more than
    once for the same function or method. Only one connection to the same method
    or function can exist.

    """

    def __init__(self, owner=None):
        """Creates the Signal.

        If owner is given (must be a keyword argument) a weak reference to it is
        kept, and this allows a Signal to be connected to another Signal. When
        the owner dies, the connection is removed.

        """
        self.listeners = []
        self._blocked = False
        self._owner = weakref.ref(owner) if owner else lambda: None

    def __get__(self, instance, cls):
        """Called when accessing as a descriptor: returns another instance."""
        if instance is None:
            return self
        try:
            return self._instances[instance]
        except AttributeError:
            self._instances = weakref.WeakKeyDictionary()
        except KeyError:
            pass
        ret = self._instances[instance] = type(self)(owner=instance)
        return ret

    def owner(self):
        """Returns the owner of this Signal, if any."""
        return self._owner()

    def connect(self, slot, priority=0, owner=None):
        """Connects a method or function ('slot') to this Signal.

        The priority argument determines the order the connected slots are
        called. A lower value calls the slot earlier.
        If owner is given, the connection will be removed if owner is garbage
        collected.

        A slot that is already connected will not be connected twice.

        If slot is an instance method (bound method), the Signal keeps no
        reference to the object the method belongs to. So if the object is
        garbage collected, the signal is automatically disconnected.

        If slot is a (normal or lambda) function, the Signal will keep a
        reference to the function. If you want to have the function disconnected
        automatically when some object dies, you should provide that object
        through the owner argument. Be sure that the connected function does not
        keep a reference to that object in that case!

        """
        key = self.makeListener(slot, owner)
        if key not in self.listeners:
            key.add(self, priority)

    def disconnect(self, func):
        """Disconnects the method or function.

        No exception is raised if there wasn't a connection.

        """
        key = self.makeListener(func)
        try:
            self.listeners.remove(key)
        except ValueError:
            pass

    def clear(self):
        """Removes all connected slots."""
        del self.listeners[:]

    @contextlib.contextmanager
    def blocked(self):
        """Returns a contextmanager that suppresses the signal.

        An example (continued from the class documentation):

        >>> o = MyObject()
        >>> o.somethingChanged.connect(receiver)
        >>> with o.somethingChanged.blocked():
        ...     o.doSomething()
        (no output)

        The doSomething() method will emit the signal but the connected slots
        will not be called.

        """
        blocked, self._blocked = self._blocked, True
        try:
            yield
        finally:
            self._blocked = blocked

    def emit(self, *args, **kwargs):
        """Emits the signal.

        Unless blocked, all slots will be called with the supplied arguments.

        """
        if not self._blocked:
            for l in self.listeners[:]:
                l.call(args, kwargs)

    __call__ = emit

    def makeListener(self, func, owner=None):
        """Returns a suitable listener for the given method or function."""
        if isinstance(func, (types.MethodType, types.BuiltinMethodType)):
            return MethodListener(func)
        elif isinstance(func, Signal):
            return FunctionListener(func, owner or func.owner())
        else:
            return FunctionListener(func, owner)


class SignalContext(Signal):
    """A Signal variant where the connected methods or functions should return
    a context manager.

    You should use the SignalContext itself also as a context manager, e.g.:

    sig = signals.SignalContext()

    with sig(args):
        do_something()

    This will first call all the connected methods or functions, and then
    enter all the returned context managers. When the context ends,
    all context managers will be exited.

    """
    def emit(self, *args, **kwargs):
        if self._blocked:
            managers = []
        else:
            managers = [l.call(args, kwargs) for l in self.listeners]
        return self.signalcontextmanager(managers)

    __call__ = emit

    @contextlib.contextmanager
    def signalcontextmanager(self, managers):
        """A context manager handling all contextmanagers from the listeners."""
        # ideas taken from Python's contextlib.nested()
        exits = []
        exc = (None, None, None)
        try:
            for m in managers:
                m.__enter__()
                exits.append(m.__exit__)
            yield
        except:
            exc = sys.exc_info()
        finally:
            while exits:
                exit = exits.pop()
                try:
                    if exit(*exc):
                        exc = (None, None, None)
                except:
                    exc = sys.exc_info()
            if exc != (None, None, None):
                raise # exc[0], exc[1], exc[2]


class ListenerBase(object):

    removeargs = 0

    def __init__(self, func, owner=None):
        self.func = func
        self.obj = owner

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

        # determine the number of arguments allowed
        end = None
        try:
            co = self.func.__code__
            if not co.co_flags & 12:
                # no *args or **kwargs are used, cut off the unwanted arguments
                end = co.co_argcount - self.removeargs
        except AttributeError:
            pass
        self.argslice = slice(0, end)


class MethodListener(ListenerBase):

    removeargs = 1

    def __init__(self, meth):
        obj = meth.__self__
        self.objid = id(meth.__self__)
        try:
            func = meth.__func__
        except AttributeError:
            # c++ methods from PyQt5 object sometimes do not have the __func__ attribute
            func = getattr(meth.__self__.__class__, meth.__name__)
        super(MethodListener, self).__init__(func, obj)

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.objid == other.objid and self.func is other.func

    def call(self, args, kwargs):
        obj = self.obj()
        if obj is not None:
            return self.func(obj, *args[self.argslice], **kwargs)


class FunctionListener(ListenerBase):

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.func is other.func

    def call(self, args, kwargs):
        return self.func(*args[self.argslice], **kwargs)


