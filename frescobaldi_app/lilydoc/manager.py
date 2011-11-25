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

from PyQt4.QtCore import QSettings, QUrl

import app
import util

from . import documentation


# cache the LilyPond Documentation instances
_documentations = None


def docs():
    """Returns the list of Documentation instances that are found."""
    global _documentations
    if _documentations is None:
        _documentations = [documentation.Documentation(url) for url in urls()]
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
    remote.sort(key=util.naturalsort)
    
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


