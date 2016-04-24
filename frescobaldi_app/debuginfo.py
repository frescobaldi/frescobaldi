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
Provides version information of important supporting modules.
"""


import functools
import sys
import os

import appinfo


def _catch_unknown(f):
    """Decorate a function, returning "unknown" on import/attribute error."""
    @functools.wraps(f)
    def wrapper():
        try:
            return f()
        except (ImportError, AttributeError):
            return "unknown"
    return wrapper


@_catch_unknown
def app_version():
    import appinfo
    return appinfo.version

@_catch_unknown
def sip_version():
    import sip
    return sip.SIP_VERSION_STR

@_catch_unknown
def pyqt_version():
    import PyQt5.QtCore
    return PyQt5.QtCore.PYQT_VERSION_STR

@_catch_unknown
def qt_version():
    import PyQt5.QtCore
    return PyQt5.QtCore.QT_VERSION_STR

@_catch_unknown
def python_version():
    import platform
    return platform.python_version()

@_catch_unknown
def operating_system():
    import platform
    return platform.platform()

@_catch_unknown
def ly_version():
    import ly.pkginfo
    return ly.pkginfo.version

@_catch_unknown
def poppler_version():
    import popplerqt5
    return '.'.join(format(n) for n in popplerqt5.poppler_version())

@_catch_unknown
def python_poppler_version():
    import popplerqt5
    return '.'.join(format(n) for n in popplerqt5.version())

if sys.platform.startswith('darwin'):
    @_catch_unknown
    def mac_installation_kind():
        import macosx
        if macosx.inside_app_bundle():
            if os.path.islink(os.getcwd() + '/../MacOS/python'):
                return 'lightweight app bundle'
            else:
                return 'standalone app bundle'
        else:
            return 'command line'


def version_info_named():
    """Yield all the relevant names and their version string."""
    yield appinfo.appname, appinfo.version
    yield "Python", python_version()
    yield "python-ly", ly_version()
    yield "Qt", qt_version()
    yield "PyQt", pyqt_version()
    yield "sip", sip_version()
    yield "poppler", poppler_version()
    yield "python-poppler-qt", python_poppler_version()
    yield "OS", operating_system()
    if sys.platform.startswith('darwin'):
        yield "installation kind", mac_installation_kind()


def version_info_string(separator='\n'):
    """Return all version names as a string, joint with separator."""
    return separator.join(map("{0[0]}: {0[1]}".format, version_info_named()))


