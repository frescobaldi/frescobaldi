# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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
import os

# By default, just return the strings unchanged
def _default(msg, plur=None, count=0):
    if plur and count != 1:
        return plur
    return msg
    
__builtin__.__dict__['_'] = _default

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
    def translate(msg, plur=None, count=0):
        if plur is not None:
            return translator.ungettext(msg, plur, count)
        else:
            return translator.ugettext(msg)
    __builtin__.__dict__['_'] = translate

def setup():
    """Install the desired language."""
    podir = __path__[0]
    for envar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        val = os.environ.get(envar)
        if val:
            for language in val.split(':'):
                mo = mofile(language)
                if mo:
                    install(mo)
                    return

setup()

