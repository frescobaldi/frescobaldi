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
Setup the application language.
"""

import locale
import re

from PyQt4.QtCore import QSettings, QTimer, QLocale

import app

from . import find, install, available
from . import qtranslator


_currentlanguage = None


def current():
    """Returns the current (user-set or default) UI language setting.
    
    A name is always returned, which can be "C", meaning no translation
    is desired.
    
    """
    language = QSettings().value("language", "", type(""))
    if not language:
        # list of system preferred locales in order of preference
        oslanguagelist = QLocale().uiLanguages()
        # list of available MO files
        applanguagelist = available()
        # append English language: an English locale/language preference
        # in oslanguagelist would otherwise be ignored
        applanguagelist.append('en')
        # remove unsupported languages (regardless of country) from oslanguagelist
        temposlanguagelist = []
        for i, oslang in enumerate(oslanguagelist):
            # in some systems, language/country codes have '-' and not '_'
            if '-' in oslang:
                oslang = re.sub('-', '_', oslang)
            if any(oslang.split('_')[0] in applang for applang in applanguagelist):
                temposlanguagelist.append(oslang)
        oslanguagelist = temposlanguagelist
        # keep the first of the supported locales in the preference order, if any
        if len(oslanguagelist) > 0:
            language = oslanguagelist[0]
    if not language:
        try:
            language = locale.getdefaultlocale()[0]
        except ValueError:
            pass
    if not language:
        language = "C"
    return language
    
    
def setup():
    """Set application language according to settings."""
    global _currentlanguage
    language = current()
    if _currentlanguage is not None and language != _currentlanguage:
        QTimer.singleShot(0, app.languageChanged)
    _currentlanguage = language
    if language != "C":
        mo = find(language)
        if mo:
            try:
                install(mo)
                return
            except Exception:
                pass
    install(None)

app.settingsChanged.connect(setup)
setup()
