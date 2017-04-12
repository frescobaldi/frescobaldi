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
Recent files handling.
"""


import os

from PyQt5.QtCore import QSettings, QUrl

import app
import qsettings

__all__ = ['urls', 'add', 'remove']


_recentfiles = None

# the maximum number of items remembered
MAXLEN = 10


def load():
    global _recentfiles
    if _recentfiles is not None:
        return
    _recentfiles = []

    urls = qsettings.get_url_list(QSettings(), "recent_files")
    for url in urls:
        if os.access(url.toLocalFile(), os.R_OK):
            _recentfiles.append(url)
    del _recentfiles[MAXLEN:]
    app.aboutToQuit.connect(save)

def save():
    QSettings().setValue("recent_files", _recentfiles)

def urls():
    load()
    return _recentfiles

def add(url):
    load()
    if url in _recentfiles:
        _recentfiles.remove(url)
    _recentfiles.insert(0, url)
    del _recentfiles[MAXLEN:]

def remove(url):
    load()
    if url in _recentfiles:
        _recentfiles.remove(url)

