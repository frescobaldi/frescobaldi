# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2010 - 2019 by Wilbert Berendsen
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
Manages locking access (across threads) to any object.

Use it for example to lock access to Poppler.Document instances.

"""

import threading
import weakref

_locks = weakref.WeakKeyDictionary()
_lock = threading.RLock()


def lock(item):
    """Return a threading.RLock instance for the given item.

    Use:

    with lock(document):
        do_something

    """
    with _lock:
        try:
            return _locks[item]
        except KeyError:
            res = _locks[item] = threading.RLock()
        return res

