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


def accessmanager():
    """Returns a global NetworkAccessManager."""
    global _accessmanager
    try:
        _accessmanager
    except NameError:
        _accessmanager = NetworkAccessManager()
    return _accessmanager


def get(url):
    """Downloads a URL, returns a QNetworkReply."""
    request = QNetworkRequest(url)
    return accessmanager().get(request)


class NetworkAccessManager(networkaccessmanager.NetworkAccessManager):
    """A NetworkAccessManager that maintains some settings from the preferences."""
    def __init__(self, parent=None):
        super(NetworkAccessManager, self).__init__(parent)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
    
    def readSettings(self):
        # TODO: set language preference from config
        langs = []
        lang = locale.getdefaultlocale()[0]
        if lang:
            langs.append(lang)
            if '_' in lang:
                langs.append(lang.split('_')[0])
        langs.append('en')
        self.headers['Accept-Language'] = ','.join(langs)



