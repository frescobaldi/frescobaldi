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
Internationalisation.
"""

import __builtin__
import os
import re

from PyQt4.QtCore import QTimer, QLocale

from . import mofile

podir = __path__[0]

def available():
    """Returns a list of language shortnames for which a MO file is available."""
    return [name[:-3] for name in os.listdir(podir) if name.endswith(".mo")]
    
def defaultLanguageFromQLocale():
    # list of system preferred locales in order of preference
    oslanguagelist = QLocale().uiLanguages()
    # list of available MO files
    applanguagelist = available()
    # append English language: an English locale/language preference
    # in oslanguagelist would otherwise be ignored
    applanguagelist.append('en')
    # remove unsupported languages (regardless of country) from oslanguagelist
    oklanguagelist = []
    for i, oslang in enumerate(oslanguagelist):
        # in some systems, language/country codes have '-' and not '_'
        if '-' in oslang:
            oslang = re.sub('-', '_', oslang)
        if any(oslang.split('_')[0] in applang for applang in applanguagelist):
            oklanguagelist.append(oslang)
    # keep the first of the supported locales in the preference order, if any
    if len(oklanguagelist) > 0:
        return oklanguagelist[0]
    
def find(language):
    """Returns a .mo file for the given language.
    
    Returns None if no suitable MO file can be found.
    
    """
    filename = os.path.join(podir, language + ".mo")
    if os.path.exists(filename):
        return filename
    elif '_' in language:
        return find(language.split('_')[0])
    
def translator(mo):
    """Returns a function that can translate messages using the specified MoFile object.
    
    The returned function can be called with one to four arguments:
    
    - message
    - context, message
    - message, plural_message, count
    - context, message, plural_message, count

    In all cases a single string (the translation) is returned.
    
    If mo is None, returns a dummy translator that returns strings untranslated.
    
    """
    if not mo:
        mo = mofile.NullMoFile()
    funcs = (None, mo.gettext, mo.pgettext, mo.ngettext, mo.npgettext)
    return lambda *args: funcs[len(args)](*args)
    
def install(filename):
    """Installs the translations from the given .mo file.
    
    If filename is None, installs a dummy translator.
    
    """
    __builtin__._ = translator(mofile.MoFile(filename) if filename else None)

