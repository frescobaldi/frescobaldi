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


import os
import sys


def inside_app_bundle():
    """Return True if we are inside a .app bundle."""
    # Testing for sys.frozen == 'macosx_app' (i.e. are we inside a .app bundle
    # packaged with py2app?) should be sufficient, but let's also check whether
    # we are inside a .app-bundle-like folder structure.
    return (getattr(sys, 'frozen', '') == 'macosx_app' or
        '.app/Contents/MacOS' in os.path.abspath(sys.argv[0]))

def use_osx_menu_roles():
    """Return True if Mac OS X-specific menu roles are to be used."""
    global _use_roles
    try:
        return _use_roles
    except NameError:
        _use_roles = inside_app_bundle()
    return _use_roles

def system_python():
    """Return a list containing the command line to run the system Python.

    (One of) the system-provided Python interpreter(s) is selected to run
    the tools included in LilyPond, e.g. convert-ly.

    The system-provided Python interpreter must be explicitly called:
    - the LilyPond-provided interpreter lacks many modules (and is
      difficult to run properly from outside the application bundle);
    - searching for the interpreter in the path is unreliable, since it
      might lack some modules or it could be an incompatible version;
      moreover if Frescobaldi is launched as an application bundle,
      the PATH variable is not set;
    - the interpreter included in Frescobaldi's application bundle,
      when present, lacks some modules.

    The earliest Python version >= 2.4 is called in 32 bit mode, for
    compatibility with midi2ly and lilysong, although Frescobaldi does not
    currently support the latter.
    In particular:
    - midi.so is 32-bit only;
    - Python >= 2.5 gives a "C API version mismatch" RuntimeWarning
      on `import midi`;
    - Python >= 2.6 gives a DeprecationWarning on `import popen2`.

    """
    for v in ['4', '5', '6', '7']:
        python = '/System/Library/Frameworks/Python.framework/Versions/2.' + v
        python += '/bin/python2.' + v
        if os.path.exists(python):
            return ['/usr/bin/arch', '-i386', python]

