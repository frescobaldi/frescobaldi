# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Utility functions.
"""

from __future__ import unicode_literals

import os
import weakref


def findexe(cmd):
    """Checks the PATH for the executable and returns the absolute path or None."""
    if os.path.isabs(cmd):
        return cmd if os.access(cmd, os.X_OK) else None
    else:
        ucmd = os.path.expanduser(cmd)
        if os.path.isabs(ucmd):
            return ucmd if os.access(ucmd, os.X_OK) else None
        elif os.sep in cmd and os.access(cmd, os.X_OK):
            return os.path.abspath(cmd)
        else:
            for p in os.environ.get("PATH", os.defpath).split(os.pathsep):
                if os.access(os.path.join(p, cmd), os.X_OK):
                    return os.path.join(p, cmd)


class cachedproperty(object):
    """Stores a value that is computed at first request and can be read and unset."""
    def __init__(self, method):
        self.method = method
        self.instances = weakref.WeakKeyDictionary()
        self.__doc__ = method.__doc__
    
    def __get__(self, instance, cls):
        if instance is None:
            return self
        try:
            return self.instances[instance]
        except KeyError:
            value = self.instances[instance] = self.method(instance)
            return value
    
    def __set__(self, instance, value):
        self.instances[instance] = value
        
    def __delete__(self, instance):
        try:
            del self.instances[instance]
        except KeyError:
            pass

