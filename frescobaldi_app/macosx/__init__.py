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

def inside_lightweight_app_bundle():
    """Return True if we are inside a lightweight .app bundle."""
    # A lightweight .app bundle (created with macosx/mac-app.py without
    # the standalone option) contains a symlink to the Python interpreter
    # instead of a copy.
    return (inside_app_bundle()
            and os.path.islink(os.getcwd() + '/../MacOS/python'))

def use_osx_menu_roles():
    """Return True if Mac OS X-specific menu roles are to be used."""
    global _use_roles
    try:
        return _use_roles
    except NameError:
        _use_roles = inside_app_bundle()
    return _use_roles

def midi_so_arch(lilypondinfo):
    """Find the midi.so library of the selected LilyPond installation,
    if it exists, and return its architecture; otherwise return None.

    """
    import subprocess
    for d in [lilypondinfo.versionString(), 'current']:
        midi_so = os.path.abspath(lilypondinfo.bindir() + '/../lib/lilypond/' + d + '/python/midi.so')
        if os.access(midi_so, os.R_OK):
            s = subprocess.run(['/usr/bin/file', midi_so], capture_output = True)
            if b'x86_64' in s.stdout:
                return 'x86_64'
            else:
                return 'i386'
    return None

def system_python(major, arch):
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
      when present, lacks some modules; moreover, Frescobaldi now uses
      Python 3, while LilyPond's tools prior to version 2.21.0 are written
      in Python 2.

    If Python 2 is requested, the earliest Python 2 version >= 2.4 is
    called, possibly avoiding the following:
    - Python >= 2.5 gives a "C API version mismatch" RuntimeWarning
      on `import midi`;
    - Python >= 2.6 gives a DeprecationWarning on `import popen2`.
    A Python 2 interpreter is always available (as of macOS 10.15 Catalina).
    If Python 3 is requested, the earliest Python 3 version >= 3.5 is
    called.

    In LilyPond <= 2.19.54 midi2ly depends on the binary library midi.so
    (replaced in 2.19.55 by a Python module), which is 32 bit in the app
    bundle distributed by LilyPond and might be in other cases as well.
    Thus, the selected Python interpreter is called with the corresponding
    architecture.
    If 32 bit architecture is required but the system Pythons do not
    support it (as is the case on macOS >= 10.15 Catalina), return None.

    """
    import platform
    mac_ver = platform.mac_ver()
    if (arch == 'i386') and (int(mac_ver[0].split('.')[1]) >= 15):
        return None
    if major == 2:
        minors = list(range(4, 8))
    elif major == 3:
        minors = list(range(5, 9))
    for minor in minors:
        version = str(major) + '.' + str(minor)
        python = '/System/Library/Frameworks/Python.framework/Versions/' + version
        python += '/bin/python' + version
        if os.path.exists(python):
            return ['/usr/bin/arch', '-' + arch, python, '-E']

