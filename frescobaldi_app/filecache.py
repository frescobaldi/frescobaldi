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
Caches information about files, and checks the mtime upon request.
"""

import os


class FileCache(object):
    """Caches information about files, and checks the mtime upon request.
    
    Has __setitem__, __getitem__ and clear methods like a dict.
    
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
    
    def clear(self):
        self._cache.clear()


