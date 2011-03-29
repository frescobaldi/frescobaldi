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
Internationalisation.
"""

import __builtin__
import gettext
import locale
import os

# By default, just return the strings unchanged
def _default(message, plural=None, count=0):
    if plural and count != 1:
        return plural
    return message

def _default_context(context, message, plural=None, count=0):
    if plural and count != 1:
        return plural
    return message

__builtin__.__dict__['_'] = _default
__builtin__.__dict__['_c'] = _default_context


podir = __path__[0]

def mofile(language):
    """Returns a .mo file for the given language.
    
    Returns None if no suitable MO file can be found.
    
    """
    mofile = os.path.join(podir, language + ".mo")
    if os.path.exists(mofile):
        return mofile
    if '_' in language:
        mofile = os.path.join(podir, language.split('_')[0] + ".mo")
        if os.path.exists(mofile):
            return mofile
    
def install(mofile):
    """Installs the translations from the given .mo file."""
    translator = gettext.GNUTranslations(open(mofile))
    
    def translate(message, plural=None, count=0):
        if plural is not None:
            return translator.ungettext(message, plural, count)
        else:
            return translator.ugettext(message)
    
    def translate_context(context, message, plural=None, count=0):
        return translate(context + "\x04" + message, plural, count)
    
    __builtin__.__dict__['_'] = translate
    __builtin__.__dict__['_c'] = translate_context

def setup():
    """Install the desired language."""
    try:
        language = locale.getdefaultlocale()[0]
    except ValueError:
        return
    if language:
        mo = mofile(language)
        if mo:
            install(mo)

setup()

