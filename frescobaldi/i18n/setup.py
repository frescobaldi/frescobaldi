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

from PyQt6.QtCore import QLocale, QSettings, QTimer
from PyQt6.QtWidgets import QMessageBox

import app

from . import install, available, UnknownLanguageError

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

    May return "C", if none of the system preferred languages is available
    in Frescobaldi. Note that this is effectively equivalent to a return of "en",
    though the latter means that English is actually requested by the user,
    not a fallback.

    """
    av_langs = available()
    av_langs.append("en")
    for lang in preferred():
        if lang in av_langs or lang.split('_')[0] in av_langs:
            return lang
    return "C"

def current():
    """Returns the currently active UI language code.

    A name is always returned, which can be "C" or "en", meaning no
    translation is desired.

    """
    return QSettings().value("language", "", str) or default()

def _setup():
    """Set application language according to settings."""
    global _currentlanguage
    new_language = current()
    try:
        install(new_language)
    except UnknownLanguageError:
        import language_names
        lang_name = language_names.languageName(new_language, "en")
        msg = """\
Frescobaldi was configured to display its interface in {language}, but the \
translation is not available. Frescobaldi will continue in English. This probably \
means you installed Frescobaldi from source and are missing the MO catalogs; \
please generate them using: \
<code>tox -e mo-generate</code>""".format(language=lang_name)
        QMessageBox.critical(None, app.caption("Error"), msg)
        new_language = "C"
        install(new_language)
    if _currentlanguage is not None and new_language != _currentlanguage:
            app.signals.languageChanged.emit()
    _currentlanguage = new_language


@app.oninit
def _start_up():
    """Initialize GUI translations. Called op app startup."""
    _setup()
    from . import qtranslator
    qtranslator.initialize()


app.settingsChanged.connect(_setup)
