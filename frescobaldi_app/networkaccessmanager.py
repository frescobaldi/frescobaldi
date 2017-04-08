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
A QNetworkAccessManager subclass with easy registration of custom url schemes.
"""


from PyQt5.QtCore import QThread, QTimer, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class NetworkAccessManager(QNetworkAccessManager):
    """A QNetworkAccessManager subclass with easy registration of custom url schemes.

    Use the registerHandler() method to add custom scheme handlers.
    The registerHtmlHandler() method is used to add a simple callable as handler that
    gets a QUrl and should return the HTML as a normal string.

    The headers instance attribute is a dictionary (empty by default) containing
    extra headers (as key, value) that are added to outgoing requests.

    """

    def __init__(self, parent=None):
        QNetworkAccessManager.__init__(self, parent)
        self._dispatcher = {}
        self.headers = {}

    def createRequest(self, operation, request, data):
        try:
            requestFunc = self._dispatcher[request.url().scheme()]
        except KeyError:
            self.addHeadersToRequest(request)
            return QNetworkAccessManager.createRequest(self, operation, request, data)
        return requestFunc(self, operation, request, data)

    def addHeadersToRequest(self, request):
        """Called on outgoing requests and should add raw headers to the request.

        The default implementation of this method simply adds all the headers in the
        headers instance attribute.

        """
        for name, value in self.headers.items():
            request.setRawHeader(bytearray(name, "latin_1"), bytearray(value, "latin_1"))

    def registerHandler(self, scheme, handler):
        """Registers a handler for the given scheme.

        The handler is called with four arguments (manager, operation, request,
        data), just like the QNetworkAccessManager.createRequest method, and
        should return a QNetworkReply instance.

        """
        self._dispatcher[scheme] = handler

    def registerHtmlHandler(self, scheme, handler, threaded=False, encoding="UTF-8"):
        """Registers a simple callable as the handler for the given scheme.

        The handler only gets a GET URL (QUrl) and should return a HTML string.
        If threaded is True, the handler is called in a background thread.
        The encoding defaults to UTF-8 and is used for encoding the HTML returned
        by then handler and also set in the Content-Type header.

        """
        cls = ThreadedHtmlReply if threaded else HtmlReply
        def createRequest(mgr, operation, request, data):
            return cls(mgr, request.url(), handler, encoding)
        self._dispatcher[scheme] = createRequest

    def unregisterHandler(self, scheme):
        """Removes the special handling for the given scheme."""
        try:
            del self._dispatcher[scheme]
        except KeyError:
            pass


class HtmlReplyBase(QNetworkReply):
    """Abstract base class for a QNetworkReply that represents a generated HTML string."""
    def __init__(self, manager, url, handler, encoding="UTF-8"):
        QNetworkReply.__init__(self, manager)
        self.setUrl(url)
        self._handler = handler
        self._encoding = encoding

    def callHandler(self):
        self._content = self._handler(self.url()).encode(self._encoding)

    def outputReady(self):
        self._offset = 0
        self.setHeader(QNetworkRequest.ContentTypeHeader, "text/html; charset={0}".format(self._encoding))
        self.setHeader(QNetworkRequest.ContentLengthHeader, len(self._content))
        self.open(QNetworkReply.ReadOnly | QNetworkReply.Unbuffered)

    def emitSignals(self):
        self.readyRead.emit()
        self.finished.emit()

    def abort(self):
        pass

    def bytesAvailable(self):
        return len(self._content) - self._offset

    def isSequential(self):
        return True

    def readData(self, maxSize):
        if self._offset < len(self._content):
            end = min(self._offset + maxSize, len(self._content))
            data = self._content[self._offset:end]
            self._offset = end
            return data


class HtmlReply(HtmlReplyBase):
    """QNetworkReply that generates a HTML string by calling handler(url).encode(encoding)."""
    def __init__(self, manager, url, handler, encoding="UTF-8"):
        HtmlReplyBase.__init__(self, manager, url, handler, encoding)
        self.callHandler()
        self.outputReady()
        QTimer.singleShot(0, self.emitSignals)


class ThreadedHtmlReply(HtmlReplyBase):
    """HtmlReply that calls handler(url) in a background thread."""
    def __init__(self, manager, url, handler, encoding="UTF-8"):
        HtmlReplyBase.__init__(self, manager, url, handler, encoding)
        self._thread = Thread(self.callHandler)
        self._thread.finished.connect(self.threadFinished)
        self._thread.start()

    def threadFinished(self):
        self.outputReady()
        self.emitSignals()


class Thread(QThread):
    """QThread that runs a single callable."""
    def __init__(self, func):
        QThread.__init__(self)
        self._func = func

    def run(self):
        self._func()


