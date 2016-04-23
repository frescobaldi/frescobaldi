# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Utility functions used in the autocomplete package.
"""


import functools
import time
import weakref


def keep(f):
    """Returns a decorator that remembers its return value for some time."""
    _delay = 5.0 # sec
    _cache = weakref.WeakKeyDictionary()
    @functools.wraps(f)
    def decorator(self, *args):
        try:
            result = _cache[self]
        except KeyError:
            pass
        else:
            t, ret = result
            if (time.time() - t) < _delay:
                return ret
        ret = f(self, *args)
        _cache[self] = (time.time(), ret)
        return ret
    return decorator


# helper functions for displaying data from models
def command(item):
    """Prepends '\\' to item."""
    return '\\' + item


def variable(item):
    """Appends ' = ' to item."""
    return item + " = "


def cmd_or_var(item):
    """Appends ' = ' to item if it does not start with '\\'."""
    return item if item.startswith('\\') else item + " = "


def make_cmds(words):
    """Returns generator prepending '\\' to every word."""
    return ('\\' + w for w in words)


