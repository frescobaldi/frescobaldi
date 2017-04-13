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
Expand variables like $DATE, $LILYPOND_VERSION etc. in snippets.
"""


import builtins
import time

import appinfo
import lilypondinfo


def _(docstring):
    """Returns a decorator.

    The decorator gives a function a doc() method, returning the translated docstring.
    The untranslated docstring will be added as __doc__ to the function.

    builtins._ is expected to be the translation function.

    We use the underscore as function name so xgettext picks up the strings
    to be translated.

    """
    def deco(f):
        f.__doc__ = docstring
        f.doc = lambda: builtins._(docstring)
        return f
    return deco


def documentation(cls):
    """Yields tuples documenting the methods of the specified class.

    The tuples are: (function_name, docstring). The docstrings are translated.
    The tuples are sorted on function_name.

    """
    for name, meth in sorted(cls.__dict__.items()):
        if name.startswith('_'):
            return
        yield name, meth.doc()


ANCHOR, CURSOR, SELECTION = constants = 1, 2, 3 # just some constants

class Expander(object):
    """Expands variables.

    The methods return text or other events (currently simply integer constants).

    """
    def __init__(self, cursor):
        self.cursor = cursor

    @_("The current date in YYYY-MM-DD format.")
    def DATE(self):
        return time.strftime('%Y-%m-%d')

    @_("The version of the default LilyPond program.")
    def LILYPOND_VERSION(self):
        return lilypondinfo.preferred().versionString()

    @_("The version of Frescobaldi.")
    def FRESCOBALDI_VERSION(self):
        return appinfo.version

    @_("The URL of the current document.")
    def URL(self):
        return self.cursor.document().url().toString()

    @_("The full local filename of the current document.")
    def FILE_NAME(self):
        return self.cursor.document().url().toLocalFile()

    @_("The name of the current document.")
    def DOCUMENT_NAME(self):
        return self.cursor.document().documentName()

    @_("Moves the text cursor here after insert.")
    def CURSOR(self):
        return CURSOR

    @_("Selects text from here to the position given using the <code>$CURSOR</code> variable")
    def ANCHOR(self):
        return ANCHOR

    @_("The selected text if available. If not, the text cursor is moved here.")
    def SELECTION(self):
        return SELECTION if self.cursor.hasSelection() else CURSOR


