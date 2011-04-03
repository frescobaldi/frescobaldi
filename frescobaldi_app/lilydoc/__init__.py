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

import network

from . import manual


def save(func):
    """Decorator that lets an instance method cache its return value.
    
    If the return value is not None, it is cached and returned next time.
    If the return value is None, nothing is cached and the method is
    called again next time.
    
    """
    _cache = weakref.WeakKeyDictionary()
    @functools.wraps(func)
    def wrapper(self):
        try:
            return _cache[self]
        except KeyError:
            result = func(self)
            if result is not None:
                _cache[self] = result
            return result
    return wrapper


class LilyDoc(object):
    """Represents one instance of the full LilyPond documentation.
    
    The url, given on instantiation, should point to the folder (local or remote)
    containing the 'VERSION' file and 'Documentation' folder.
    
    """
    def __init__(self, url):
        self._url = url
        self._localFile = url.toLocalFile()
        self._versionRequest = None
        
    def url(self):
        return QUrl(self._url)
    
    def isLocal(self):
        """Returns True if the documentation is on the local system."""
        return bool(self._localFile)
    
    def version(self):
        """Returns the versionString as a tuple of ints."""
        v = self.versionString()
        if v is not None:
            return tuple(map(int, re.findall(r"\d+", v)))
    
    @save
    def versionString(self):
        """Returns the version, if it can be found, of this manual. If not, returns an empty string."""
        if self.isLocal():
            verfile = os.path.join(self._localFile, 'VERSION')
            if os.path.exists(verfile) and os.access(verfile, os.R_OK):
                return file(verfile).read().strip()
            return ""
        if self._versionRequest is None:
            url = self.url()
            sep = '/' if not url.path().endswith('/') else ''
            url.setPath(url.path() + sep + 'VERSION')
            self._versionRequest = network.get(url)
        elif self._versionRequest.isFinished():
            v = str(self._versionRequest.readAll()).strip()
            self._versionRequest = None
            return v
        
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




