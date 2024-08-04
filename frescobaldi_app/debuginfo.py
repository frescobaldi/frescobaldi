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
import platform
import os

import app
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
def pyqt_version():
    import PyQt6.QtCore
    return PyQt6.QtCore.PYQT_VERSION_STR

@_catch_unknown
def qt_version():
    import PyQt6.QtCore
    return PyQt6.QtCore.QT_VERSION_STR

@_catch_unknown
def python_version():
    return platform.python_version()

@_catch_unknown
def operating_system():
    plat = platform.platform()
    if platform.system() == "Linux":
        try:
            distro = platform.freedesktop_os_release()["PRETTY_NAME"]
        except OSError:
            # play it safe
            distro = "unknown distribution"
        return f"{plat} ({distro})"
    else:
        return plat

@_catch_unknown
def ly_version():
    import ly.pkginfo
    return ly.pkginfo.version

@_catch_unknown
def qpageview_version():
    import qpageview
    return qpageview.version_string

@_catch_unknown
def poppler_version():
    import popplerqt5
    return '.'.join(format(n) for n in popplerqt5.poppler_version())

@_catch_unknown
def python_poppler_version():
    import popplerqt5
    return '.'.join(format(n) for n in popplerqt5.version())

if platform.system() == "Darwin":
    @_catch_unknown
    def mac_installation_kind():
        import macos
        if macos.inside_lightweight_app_bundle():
            return 'lightweight .app bundle'
        elif macos.inside_app_bundle():
            return 'standalone .app bundle'
        else:
            return 'command line'

elif platform.system() == "Linux":
    @_catch_unknown
    def linux_installation_kind():
        import linux
        if linux.inside_flatpak():
            return "Flatpak"
        else:
            return "distro package or installed from source"

def version_info_named():
    """Yield all the relevant names and their version string."""
    yield appinfo.appname, appinfo.version
    yield "Extension API", appinfo.extension_api
    yield "Python", python_version()
    if app.is_git_controlled():
        import vcs
        repo = vcs.app_repo
        yield "Git branch", repo.active_branch()
        commit = repo.run_command(
            'log',
            ['-n', '1', '--format=format:%h'])
        yield "on commit", commit[0]
    yield "python-ly", ly_version()
    yield "Qt", qt_version()
    yield "PyQt", pyqt_version()
    yield "qpageview", qpageview_version()
    yield "poppler", poppler_version()
    yield "python-poppler-qt", python_poppler_version()
    yield "OS", operating_system()
    if platform.system() == 'Darwin':
        yield "installation kind", mac_installation_kind()
    elif platform.system() == "Linux":
        yield "Installation kind", linux_installation_kind()


def version_info_string(separator='\n'):
    """Return all version names as a string, joint with separator."""
    return separator.join(map("{0[0]}: {0[1]}".format, version_info_named()))
