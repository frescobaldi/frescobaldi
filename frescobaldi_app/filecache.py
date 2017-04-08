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
Caches information about files, and checks the mtime upon request.
"""


import os
import weakref


class FileCache(object):
    """Caches information about files, and checks the mtime upon request.

    Has __setitem__, __getitem__, __delitem__, clear etc. methods like a dict.

    """
    def __init__(self):
        self._cache = {}

    def __getitem__(self, filename):
        mtime, value = self._cache[filename]
        try:
            if mtime == os.path.getmtime(filename):
                return value
        except (IOError, OSError):
            pass
        del self._cache[filename]
        raise KeyError

    def __setitem__(self, filename, value):
        try:
            self._cache[filename] = (os.path.getmtime(filename), value)
        except (IOError, OSError):
            pass

    def __delitem__(self, filename):
        del self._cache[filename]

    def __contains__(self, filename):
        try:
            self[filename]
            return True
        except KeyError:
            return False

    def filename(self, value):
        """Returns the filename of the cached value (if available)."""
        for filename in self.filenames():
            mtime, obj = self._cache[filename]
            if obj == value:
                return filename

    def filenames(self):
        """Yields filenames that are still valid in the cache."""
        for filename in list(self._cache):
            try:
                self[filename]
                yield filename
            except KeyError:
                pass

    def clear(self):
        self._cache.clear()


class WeakFileCache(FileCache):
    """Caches information about files like FileCache, but with a weak reference.

    This means the object is discarded if you don't keep a reference to it
    elsewhere.

    """
    def __getitem__(self, filename):
        mtime, valueref = self._cache[filename]
        value = valueref()
        if value is not None:
            try:
                if mtime == os.path.getmtime(filename):
                    return value
            except (IOError, OSError):
                pass
        del self._cache[filename]
        raise KeyError

    def __setitem__(self, filename, value):
        valueref = weakref.ref(value)
        try:
            self._cache[filename] = (os.path.getmtime(filename), valueref)
        except (IOError, OSError):
            pass


