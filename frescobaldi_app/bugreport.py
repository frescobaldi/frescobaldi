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
Functions to compose a bugreport via e-mail and to get version information.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QUrl

import helpers
import appinfo


def versionInfo():
    """Returns version and platform information as a dict for debugging purposes."""
    try:
        import sip
        sip_version = sip.SIP_VERSION_STR
    except (ImportError, NameError):
        sip_version = "unknown"
    
    try:
        import PyQt4.QtCore
        pyqt_version = PyQt4.QtCore.PYQT_VERSION_STR
    except (ImportError, NameError):
        pyqt_version = "unknown"
    
    try:
        qt_version = PyQt4.QtCore.QT_VERSION_STR
    except NameError:
        qt_version = "unknown"
    
    try:
        import platform
        python_version = platform.python_version()
        osname = platform.platform()
    except (ImportError, NameError):
        python_version = "unknown"
        osname = "unknown"
    
    try:
        import ly.pkginfo
        ly_version = ly.pkginfo.version
    except (ImportError, NameError):
        ly_version = "unknown"
    
    try:
        import popplerqt4
        poppler_version = '.'.join(str(n) for n in popplerqt4.poppler_version())
        python_poppler_version = '.'.join(str(n) for n in popplerqt4.version())
    except ImportError:
        poppler_version = "unknown"
        python_poppler_version = "missing"
    except AttributeError:
        poppler_version = "unknown"
        python_poppler_version = "unknown"

    return locals()


def versionInfoString():
    """Returns the information from versionInfo() formatted as a terse string."""
    return (
        "Python: {python_version} -- "
        "Qt: {qt_version} -- "
        "PyQt4: {pyqt_version} -- "
        "sip: {sip_version}\n"
        "python-ly: {ly_version}\n"
        "poppler: {poppler_version} -- "
        "python-poppler-qt4: {python_poppler_version}\n"
        "OS: {osname}".format(**versionInfo()))
    

def email(subject, body):
    """Opens the e-mail composer with the given subject and body, with version information added to it."""
    subject = "[{0} {1}] {2}".format(appinfo.appname, appinfo.version, subject)
    body = "{0}: {1}\n\n{2}\n\n{3}\n\n".format(appinfo.appname, appinfo.version, versionInfoString(), body)
    url = QUrl("mailto:" + appinfo.maintainer_email)
    url.addQueryItem("subject", subject)
    url.addQueryItem("body", body)
    helpers.openUrl(url, "email")

