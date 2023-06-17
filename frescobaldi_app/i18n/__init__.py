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
Internationalization of Frescobaldi.
"""

import builtins
import gettext
from pathlib import Path

modir = __path__[0]

def available():
    """Returns a list of language shortnames for which a MO file is available."""
    return [str(path.parent.stem) for path in Path(modir).rglob("LC_MESSAGES")]

def translator(language):
    """Returns a function that can translate messages using the specified language.

    The value "C" causes a dummy translator that returns English strings untranslated to be
    returned. Otherwise, the language must have a translation, meaning that either `language`
    or `language.split('_')[0]` is in the list returned by `available()`.

    The returned function can be called with one to four arguments:

    - message
    - context, message
    - message, plural_message, count
    - context, message, plural_message, count

    In all cases a single string (the translation) is returned.
    """
    if language == "C":
        catalog = gettext.NullTranslations()
    else:
        assert language in available() or language.split('_')[0] in available()
        catalog = gettext.translation("frescobaldi", localedir=modir,
                                      languages=[language])
    funcs = (None, catalog.gettext, catalog.pgettext, catalog.ngettext, catalog.npgettext)
    return lambda *args: funcs[len(args)](*args)

def install(language):
    """Installs the translations for the given language."""
    builtins._ = translator(language)
