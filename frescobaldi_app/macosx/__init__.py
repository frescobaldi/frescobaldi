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
Functions that have to do with Mac OS X-specific behaviour.

Importing this package does nothing; the macosx.setup module sets up
the Mac OS X-specific behaviour, such as the global menu and the file open event
handler, etc.

"""

from __future__ import unicode_literals

import os
import sys


def is_osx():
    """Return True if we are running on Mac OS X."""
    return sys.platform.startswith('darwin')

def use_osx_menu_roles():
    """Return True if Mac OS X-specific menu roles are to be used."""
    global _use_roles
    try:
        return _use_roles
    except NameError:
        _use_roles = (getattr(sys, 'frozen', '') == 'macosx_app'
            or ('.app/Contents/MacOS' in os.path.abspath(sys.argv[0])))
    return _use_roles

