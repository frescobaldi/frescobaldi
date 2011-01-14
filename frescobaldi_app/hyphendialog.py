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

from __future__ import unicode_literals

"""
Dialog for selecting a hyphen language.
"""

import glob
import os

from PyQt4.QtCore import QSettings

import app
import language_names


# paths to check for hyphen dicts
default_paths = [
    "share/hyphen",
    "share/myspell",
    "share/myspell/dicts",
    "share/dict/ooo",
    "share/apps/koffice/hyphdicts",
    "lib/scribus/dicts",
    "share/scribus/dicts",
    "share/scribus-ng/dicts",
    "share/hunspell",
]


def settings():
    """Returns the QSettings group for our settings."""
    settings = QSettings()
    settings.beginGroup("hyphenation")
    return settings

def paths():
    """ Yields a list of paths based on config """
    # prefixes to look in for relative paths
    prefixes = ['/usr/', '/usr/local/']
    
    def gen():
        # if the path is not absolute, add it to all prefixes.
        for path in settings().value("paths", default_paths) or []:
            if os.path.isabs(path):
                yield path
            else:
                for pref in prefixes:
                    yield os.path.join(pref, path)
    return filter(os.path.isdir, gen())

def findDicts():
    """ Find installed hyphen dictionary files """
    
    # now find the hyph_xx_XX.dic files
    dicfiles = (f for p in paths()
                  for f in glob(os.path.join(p, 'hyph_*.dic')) if os.access(f, os.R_OK))

    return dict((os.path.basename(dic)[5:-4], dic) for dic in dicfiles)


class HyphenDialog():
    def __init__(self, mainwindow):
        pass
    
    def hyphenator(self):
        import hyphenator
        #TODO: further implement this.
        return hyphenator.Hyphenator('/usr/share/hyphen/hyph_nl_NL.dic')

