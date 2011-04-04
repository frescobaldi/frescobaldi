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
Network-related utility functions.
"""

import locale

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

import app
import networkaccessmanager

_accessmanager = None


def accessmanager():
    """Returns a global NetworkAccessManager."""
    global _accessmanager
    if _accessmanager:
        return _accessmanager
    _accessmanager = networkaccessmanager.NetworkAccessManager()
    _readSettings()
    app.settingsChanged.connect(_readSettings)
    return _accessmanager


def get(url):
    request = QNetworkRequest(url)
    return accessmanager().get(request)



def _readSettings():
    """Called when the networkaccessmanager is created for the first time and when the app settings change."""
    nam = _accessmanager
    
    # TODO: set language preference from config
    langs = []
    lang = locale.getdefaultlocale()[0]
    if lang:
        langs.append(lang)
        if '_' in lang:
            langs.append(lang.split('_')[0])
    langs.append('en')
    nam.headers['Accept-Language'] = ','.join(langs)



