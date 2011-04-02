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

from __future__ import unicode_literals

"""
Manages LilyPond Documentation.
"""


import functools
import os
import re
import weakref

from PyQt4.QtCore import QUrl

from . import manual


def save(func):
    """Decorator that lets a method cache its return value and return that next calls."""
    _cache = weakref.WeakKeyDictionary()
    @functools.wraps(func)
    def wrapper(self):
        try:
            return _cache[self]
        except KeyError:
            result = _cache[self] = func(self)
            return result
    return wrapper


class LilyDoc(object):
    """Represents one instance of the full LilyPond documentation."""
    def __init__(self, url):
        self._url = url
    
    def url(self):
        return self._url
    
    def isLocal(self):
        """Returns True if the documentation is on the local system."""
        return bool(self._url.toLocalFile())
        
    def version(self):
        """Returns the versionString as a tuple of ints."""
        return tuple(map(int, re.findall(r"\d+", self.versionString())))
    
    @save
    def versionString(self):
        """Returns the version, if it can be found, of this manual. If not, returns an empty string."""
        if self.isLocal():
            verfile = os.path.join(self.baseUrl().toLocalFile(), 'VERSION')
            if os.path.exists(verfile):
                return open(verfile).read().strip()
        return ""

    def baseUrl(self):
        """Tries to find the top directory of this documentation."""
        filename = self.url().toLocalFile()
        if filename:
            # local url
            while os.sep in filename:
                if os.path.isdir() and os.path.exists(os.path.join(filename, 'VERSION'):
                    return QUrl.fromLocalFile(filename)
                filename = os.path.dirname(filename)
        return self._url
        
    @save
    def notation(self):
        """Returns a searchable instance of the Notation Manual."""
        return manual.NotationManual(self)
        
    @save
    def learning(self):
        """Returns a searchable instance of the Learning Manual."""
        return manual.LearningManual(self)
        
    @save
    def internals(self):
        """Returns a searchable instance of the Internals Reference."""
        return manual.InternalsReference(self)




