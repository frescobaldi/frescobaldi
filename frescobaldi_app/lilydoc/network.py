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
Network-related utility functions for LilyPond Documentation.
"""

from PyQt5.QtCore import QSettings
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

import app
import po
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


def langs():
    """Returns a list of language codes wished for documentation.

    If the list is empty, english (untranslated) is assumed.
    If a language code also has a country suffix, a hyphen will be used
    as separator (as required per RFC2616, Accept-Language header).

    """
    s = QSettings()
    langs = []
    lang = s.value("documentation/language", "default", str)

    if lang == "default":
        lang = s.value("language", "", str)
    if lang and lang != "C":
        langs.append(lang)
    langs.extend(po.setup.preferred())

    # now fixup the list, remove dups and
    # language/country codes in Accept-Language headers must have '-' and not '_'
    result = []
    def add(item):
        if item not in result:
            result.append(item)
    for l in langs:
        # if there is a language/country code, insert also the generic language code
        if '_' in l:
            add(l.replace('_', '-'))
            add(l.split('_')[0])
        else:
            add(l)
    return result


class NetworkAccessManager(networkaccessmanager.NetworkAccessManager):
    """A NetworkAccessManager that maintains some settings from the preferences."""
    def __init__(self, parent=None):
        super(NetworkAccessManager, self).__init__(parent)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        l = langs()
        if 'en' not in l:
            l.append('en')
        self.headers['Accept-Language'] = ','.join(l)



