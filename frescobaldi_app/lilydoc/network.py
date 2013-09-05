# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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

import locale
import re

from PyQt4.QtCore import QSettings, QLocale
from PyQt4.QtNetwork import QNetworkReply, QNetworkRequest

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


def langs():
    """Returns a list of language codes wished for documentation.
    
    If the list is empty, english (untranslated) is assumed.
    
    """
    s = QSettings()
    lang = s.value("documentation/language", "default", type(""))
    if lang == "C":
        return []
    elif lang == "default":
        lang = s.value("language", "", type(""))
        if not lang:
            # list of system preferred locales in order of preference
            lang = QLocale().uiLanguages()
        if not lang:
            try:
                lang = [locale.getdefaultlocale()[0]]
            except ValueError:
                return []
        if not lang or lang == "none":
            return []
    if isinstance(lang, basestring):
        lang = [lang]
    for i, l in enumerate(lang):
        # language/country codes in Accept-Language headers must have '-' and not '_'
        if '_' in l:
            l = re.sub('_', '-', l)
        # if there is a language/country code, insert also the generic language code
        if '-' in l:
            lang[i] = l
            lsplit = l.split('-')[0]
            if lsplit not in lang:
                lang.insert(i + 1, lsplit)
    return lang


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



