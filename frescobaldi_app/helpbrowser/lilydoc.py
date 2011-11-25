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
Manage access to LilyPond documentation.
"""

from __future__ import unicode_literals

import os
import re

from PyQt4.QtCore import pyqtSignal, QObject, QSettings, QUrl

import app
import network
import util

# cache the LilyPond Documentation instances
_documentations = None


def docs():
    """Returns the list of Documentation instances that are found."""
    global _documentations
    if _documentations is None:
        _documentations = [Documentation(url) for url in urls()]
    return list(_documentations)


def clear():
    """Clears the cached documentation instances."""
    global _documentations
    _documentations = None

app.settingsChanged.connect(clear, -100)


def urls():
    """Returns a list of QUrls where documentation can be found.
    
    Remote urls (from the users settings) are not checked but simply returned.
    For user-set local directories, if the directory itself does not contain
    LilyPond documentation, all directories one level deep are searched.
    
    This makes it possible to set one directory for local documentation and
    put there multiple sets of documentation in subdirectories (e.g. with the
    version number in the path name).
    
    The paths in the settings are read, and also the usual system directories
    are scanned.
    
    """
    user_paths = QSettings().value("documentation/paths", []) or []
    system_prefixes = [p for p in (
        '/usr',
        '/usr/local',
        '/usr/share/doc',
        '/usr/doc',
    ) if os.path.isdir(p)]
    # split in local and non-local ones (local are preferred)
    user_prefixes = []
    local = []
    remote = []
    for p in user_paths:
        user_prefixes.append(p) if os.path.isdir(p) else remote.append(p)
    
    # now find all instances of LilyPond documentation in the local paths
    def paths(path):
        """Yields possible places where LilyPond documentation could live."""
        yield path
        path = os.path.join(path, 'share', 'doc', 'lilypond', 'html')
        yield path
        yield os.path.join(path, 'offline-root')
    
    def find(path):
        """Finds LilyPond documentation."""
        for p in paths(path):
            if os.path.isdir(os.path.join(p, 'Documentation')):
                return p
    
    # search in the user-set directories, if no docs, scan one level deeper
    for p in user_prefixes:
        n = find(p)
        if n:
            local.append(n)
        elif p not in system_prefixes:
            for name, dirs, files in os.walk(p):
                for d in sorted(dirs, key=util.naturalsort):
                    n = find(os.path.join(p, d))
                    if n:
                        local.append(n)
                break
    # now add the system directories if documentation is found there
    for p in system_prefixes:
        if p not in user_prefixes:
            n = find(p)
            if n:
                local.append(n)
    urls = []
    urls.extend(map(QUrl.fromLocalFile, local))
    urls.extend(map(QUrl, remote))
    if not urls:
        urls.append(QUrl("http://lilypond.org/doc/stable"))
    return urls



class Documentation(QObject):
    """An instance of LilyPond documentation."""
    versionLoaded = pyqtSignal(bool)
    
    def __init__(self, url):
        QObject.__init__(self)
        self._url = url
        self._localFile = url.toLocalFile()
        self._versionString = None
        
        # determine version
        url = self.url()
        sep = '/' if not url.path().endswith('/') else ''
        url.setPath(url.path() + sep + 'VERSION')
        reply = self._versionReply = network.get(url)
        if reply.isFinished():
            self._versionReplyFinished()
        else:
            reply.finished.connect(self._versionReplyFinished)
    
    def url(self):
        return QUrl(self._url)
    
    def home(self):
        """Returns the url with 'Documentation' appended."""
        url = self.url()
        sep = '/' if not url.path().endswith('/') else ''
        url.setPath(url.path() + sep + 'Documentation')
        if self.version() is not None and self.version() >= (2, 14):
            url.setPath(url.path() + '/web/manuals')
        else:
            url.setPath(url.path() + '/index')
        return url
    
    def _versionReplyFinished(self):
        if self._versionReply.error():
            self._versionString = ''
        else:
            self._versionString = bytes(self._versionReply.readAll()).strip()
        self.versionLoaded.emit(bool(self._versionString))
        self._versionReply.deleteLater()
    
    def versionString(self):
        """Returns the version as a string.
        
        If the version is not yet determined, returns None.
        If the version could not be determined, returns the empty string.
        
        """
        return self._versionString
    
    def version(self):
        """Returns the version as a tuple of ints.
        
        If the version is not yet determined, returns None.
        If the version could not be determined, returns the empty tuple.
        
        """
        if self._versionString is not None:
            return tuple(map(int, re.findall(br"\d+", self._versionString)))
    
    def isLocal(self):
        """Returns True if the documentation is on the local system."""
        return bool(self._localFile)


