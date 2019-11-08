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
Setup the application language.

Also contains a function to get language preferences from the operation
system.

"""

import locale

from PyQt5.QtCore import QLocale, QSettings, QTimer

import app

from . import find, install, available

__all__ = ['preferred', 'current', 'default']


_currentlanguage = None


def preferred():
    """Return a list of language codes from the operating system preferences.

    Language- and country codes will always be separated with an underscore '_'.

    """
    try:
        langs = QLocale().uiLanguages()
    except AttributeError:
        # QLocale.uiLanguages is not in Qt 4.7 (only Qt4.8+)
        langs = []
    else:
        # in some systems, language/country codes have '-' and not '_'
        langs = [l.replace('-', '_') for l in langs]
    if not langs:
        try:
            langs.append(locale.getdefaultlocale()[0])
        except ValueError:
            pass
    return langs

def default():
    """Return the first preferred system default UI language that is available in Frescobaldi.

    May return None, if none of the system preferred languages is available
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
    return QSettings().value("language", "", str) or default() or "C"

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
            install(mo)
            return
    install(None)

@app.oninit
def _start_up():
    """Initialize GUI translations. Called op app startup."""
    _setup()
    from . import qtranslator
    qtranslator.initialize()


app.settingsChanged.connect(_setup)

