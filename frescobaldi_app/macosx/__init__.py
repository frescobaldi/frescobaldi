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
Functions that have to do with macOS-specific behaviour.

Importing this package does nothing; the macosx.setup module sets up
the macOS-specific behaviour, such as the global menu and the file open event
handler, etc.

"""


import os
import sys


def inside_app_bundle():
    """Return True if we are inside a .app bundle."""
    # Testing for sys.frozen == 'macosx_app' (i.e. are we inside a .app bundle
    # packaged with py2app?) should be sufficient, but let's also check whether
    # we are inside a .app-bundle-like folder structure.
    return (getattr(sys, 'frozen', '') == 'macosx_app' or
        '.app/Contents/MacOS' in os.path.abspath(sys.argv[0]))

def inside_lightweight_app_bundle():
    """Return True if we are inside a lightweight .app bundle."""
    # A lightweight .app bundle (created with macosx/mac-app.py without
    # the standalone option) contains a symlink to the Python interpreter
    # instead of a copy.
    return (inside_app_bundle()
            and os.path.islink(os.getcwd() + '/../MacOS/python'))

def use_osx_menu_roles():
    """Return True if macOS-specific menu roles are to be used."""
    global _use_roles
    try:
        return _use_roles
    except NameError:
        _use_roles = inside_app_bundle()
    return _use_roles
