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
Manage access to LilyPond documentation.
"""


import os

from PyQt5.QtCore import QSettings, QUrl

import app
import util
import signals
import qsettings

from . import documentation


# cache the LilyPond Documentation instances
_documentations = None


allLoaded = signals.Signal()


def docs():
    """Returns the list of Documentation instances that are found."""
    global _documentations
    if _documentations is None:
        _documentations = [documentation.Documentation(url) for url in urls()]
        _sort_docs()
        # check whether they need to fully load their version number yet
        _check_doc_versions()
    return list(_documentations)


def clear():
    """Clears the cached documentation instances."""
    global _documentations
    _documentations = None


app.settingsChanged.connect(clear, -100)


def loaded():
    """Returns True if all Documentation are loaded (i.e. know their version).

    If this function returns False, you can connect to the allLoaded signal
    to get a notification when all Documentation instances have loaded their
    version information. This signal will only be emitted once, after that all
    connections will be removed from the signal.

    """
    for d in docs():
        if d.versionString() is None:
            return False
    return True


def _check_doc_versions():
    """Checks if all documentation instances have their version loaded.

    Emits the allLoaded signal when all are loaded, also sorts the documentation
    instances then on local/remote and then version number.

    """
    for d in _documentations:
        if d.versionString() is None:
            def makefunc(doc):
                def func():
                    doc.versionLoaded.disconnect(func)
                    _check_doc_versions()
                return func
            d.versionLoaded.connect(makefunc(d))
            return
    _sort_docs()
    allLoaded.emit()
    allLoaded.clear()


def _sort_docs():
    """Sorts all documentation instances on local/remote and then version."""
    _documentations.sort(key = lambda d: (not d.isLocal(), d.version() or ()))


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
    user_paths = qsettings.get_string_list(QSettings(), "documentation/paths")
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


