# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2016 by Wilbert Berendsen
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
Cache logic.
"""

import weakref
import time


class Entry:
    def __init__(self, obj):
        self.obj = obj
        self.time = time.time()


class Cache:
    def __init__(self):
        self._cache = weakref.WeakKeyDictionary()
    
    def clear(self):
        self._cache.clear()
    
    def get(self, key):
        try:
            result = self._cache[key.group][key.page][key.size]
        except KeyError:
            return
        return result.obj
    
    def set(self, key, value):
        self._cache.setdefault(
            key.group, {}).setdefault(key.page, {})[key.size] = Entry(value)

    def closest(self, key):
        try:
            entries = self._cache[key.group][key.page].items()
        except KeyError:
            return
        # find the closest size (assuming aspect ratio has not changed)
        if entries:
            width = key.size[0]
            sizes = sorted(entries, key=lambda s: abs(1 - s[0] / width))
            return entries[sizes[0]].obj

