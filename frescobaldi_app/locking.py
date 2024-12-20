# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2024 by Benjamin Johnson
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
Manages locking access across threads.
"""

from PyQt6.QtCore import QObject, QMutex


class RLock(QObject):
    """Reentrant lock using QMutex.

    The first thread to acquire the lock becomes its owner,
    which may then safely acquire it again. The lock's
    "recursion level" respectively increases and decreases
    each time the owner acquires or releases it. The lock is
    unlocked when its "recursion level" reaches zero.

    Other threads may acquire the lock once each. Acquiring
    it again from a non-owning thread will cause deadlock.

    The easiest way to use this is as a context manager for
    the "with" statement.

    This class is loosely modeled on the standard library's
    threading.RLock, but omits most of the advanced features
    that aren't needed by Frescobaldi.

    """
    def __init__(self):
        super().__init__()
        self._mutex = QMutex()
        self._owner = None
        self._count = 0

    def acquire(self):
        """Acquire the lock."""
        thread = self.thread()
        if self._owner is None:
            self._mutex.lock()
            self._owner = thread    # weakref won't work here
            self._count = 1
        elif thread == self._owner:
            self._count += 1
        else:
            self._mutex.lock()

    __enter__ = acquire

    def release(self):
        """Release the lock."""
        thread = self.thread()
        if thread == self._owner:
            self._count -= 1
            if self._count == 0:
                self._owner = None
                self._mutex.unlock()
        else:
            self._mutex.unlock()

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def locked(self):
        """Returns True if the lock is acquired."""
        return self._count > 0


class LockMixin:
    """Mixin to add locking support to any class.

    This provides a locking.RLock, accessed through the
    lock() method, that you can use as a context manager
    to make other methods thread-safe.

    Add this mixin to classes whose instances may be
    accessed simultaneously from multiple threads.

    """
    def lock(self):
        """Returns a locking.RLock instance for this object.

        Use the return value as a context manager in methods that
        need to be thread-safe, like so:

            def someProperty(self):
                with self.lock():
                    ...your logic goes here...

        The lock is created the first time this method is called.

        """
        try:
            return self._lock
        except AttributeError:
            self._lock = RLock()
            return self._lock
