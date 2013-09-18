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

Also contains a function to get language preferences from the operation
system.

"""

import locale

from PyQt4.QtCore import QLocale, QSettings, QTimer

import app

from . import find, install, available
from . import qtranslator

__all__ = ['preferred', 'current', 'default']


_currentlanguage = None


def preferred():
    """Return a list of language codes from the operating system preferences.
    
    Language- and country codes will always be separated with an underscore '_'.
    
    """
    langs = []
    for lang in QLocale().uiLanguages():
        # in some systems, language/country codes have '-' and not '_'
        langs.append(lang.replace('-', '_'))
    if not langs:
        try: 
            langs.append(locale.getdefaultlocale()[0])
        except ValueError:
            pass
    return langs

def default():
    """Return the first preferred system default UI language that is available in Frescobaldi.
    
    May return None, if none of the system preferred languages is avaiable
    in Frescobaldi.
    
    """
    av_langs = available()
    av_langs.append("en")
    for lang in preferred():
        if lang in av_langs or lang.split('_')[0] in av_langs:
            return lang

def current():
    """Returns the currently active UI language code.
    
    A name is always returned, which can be "C", meaning no translation
    is desired.
    
    """
    return QSettings().value("language", "", type("")) or default() or "C"

def _setup():
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

app.settingsChanged.connect(_setup)
_setup()
