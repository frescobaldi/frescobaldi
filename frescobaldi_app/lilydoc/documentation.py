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
Manage access to LilyPond documentation.
"""


import os
import re

from PyQt5.QtCore import pyqtSignal, QObject, QUrl
from PyQt5.QtNetwork import QNetworkRequest

from . import network


class Documentation(QObject):
    """An instance of LilyPond documentation."""
    versionLoaded = pyqtSignal(bool)

    def __init__(self, url):
        QObject.__init__(self)
        self._url = url
        self._localFile = url.toLocalFile()
        self._versionString = None

        # determine version
        url = self.url()
        sep = '/' if not url.path().endswith('/') else ''
        url.setPath(url.path() + sep + 'VERSION')
        self._request(url)

    def _request(self, url):
        """Request a URL to read the version from."""
        reply = self._reply = network.get(url)
        if reply.isFinished():
            self._handleReply()
        else:
            reply.finished.connect(self._handleReply)

    def _handleReply(self):
        self._reply.deleteLater()
        if self._reply.error():
            self._versionString = ''
        else:
            # HTTP redirect?
            url = self._reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
            if url is not None:
                if url.path().endswith('/VERSION'):
                    self._request(self._reply.url().resolved(url))
                    return
                else:
                    # the redirect was not to a VERSION file, discard it
                    self._versionString = ''
            else:
                v = bytes(self._reply.readAll()).strip()
                if v.startswith(b'<'):
                    # probably some HTML network error message
                    self._versionString = ''
                else:
                    self._versionString = v[:16].decode('utf-8', 'replace')
        self.versionLoaded.emit(bool(self._versionString))

    def url(self):
        return QUrl(self._url)

    def home(self):
        """Returns the url with 'Documentation' appended."""
        url = self.url()
        sep = '/' if not url.path().endswith('/') else ''
        url.setPath(url.path() + sep + 'Documentation')
        if self.version() is not None and self.version() >= (2, 13, 8):
            url.setPath(url.path() + '/web/manuals')
        else:
            url.setPath(url.path() + '/index')
        return url

    def versionString(self):
        """Returns the version as a string.

        If the version is not yet determined, returns None.
        If the version could not be determined, returns the empty string.

        """
        return self._versionString

    def version(self):
        """Returns the version as a tuple of ints.

        If the version is not yet determined, returns None.
        If the version could not be determined, returns the empty tuple.

        """
        if self._versionString is not None:
            return tuple(map(int, re.findall(r"\d+", self._versionString)))

    def isLocal(self):
        """Returns True if the documentation is on the local system."""
        return bool(self._localFile)


