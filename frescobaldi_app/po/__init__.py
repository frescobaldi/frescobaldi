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
import os

from . import mofile

_default_translation = [
    lambda: None,
    lambda message: message,
    lambda context, message: message,
    lambda message, plural, count: message if count == 1 else plural,
    lambda context, message, plural, count: message if count == 1 else plural,
]

# By default, just return the strings unchanged
translation = _default_translation

# Make the _() function available everywhere 
__builtin__.__dict__['_'] = lambda *args: translation[len(args)](*args)


podir = __path__[0]

def available():
    """Returns a list of language shortnames for which a MO file is available."""
    return [name[:-3] for name in os.listdir(podir) if name.endswith(".mo")]
 
def find(language):
    """Returns a .mo file for the given language.
    
    Returns None if no suitable MO file can be found.
    
    """
    filename = os.path.join(podir, language + ".mo")
    if os.path.exists(filename):
        return filename
    elif '_' in language:
        return find(language.split('_')[0])
    
def install(filename):
    """Installs the translations from the given .mo file."""
    global translation
    translator = mofile.MoFile(filename)
    translation = [
        lambda: None,
        translator.gettext,
        translator.pgettext,
        translator.ngettext,
        translator.npgettext,
    ]

def remove():
    """Removes installed translations, reverting back to untranslated."""
    global translation
    translation = _default_translation


