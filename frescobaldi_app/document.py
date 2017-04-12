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
A Frescobaldi document.

This contains the text the user can edit in Frescobaldi. In most cases it will
be a LilyPond source file, but other file types can be used as well.

"""


import os

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QTextCursor, QTextDocument
from PyQt5.QtWidgets import QPlainTextDocumentLayout

import app
import util
import variables
import signals


class Document(QTextDocument):

    urlChanged = signals.Signal() # new url, old url
    closed = signals.Signal()
    loaded = signals.Signal()
    saving = signals.SignalContext()
    saved = signals.Signal()

    @classmethod
    def load_data(cls, url, encoding=None):
        """Class method to load document contents from an url.

        This is intended to open a document without instantiating one
        if loading the contents fails.

        This method returns the text contents of the url as decoded text,
        thus a unicode string.

        The line separator is always '\\n'.

        """
        filename = url.toLocalFile()

        # currently, we do not support non-local files
        if not filename:
            raise IOError("not a local file")
        with open(filename, 'rb') as f:
            data = f.read()
        text = util.decode(data, encoding)
        return util.universal_newlines(text)

    @classmethod
    def new_from_url(cls, url, encoding=None):
        """Create and return a new document, loaded from url.

        This is intended to open a new Document without instantiating one
        if loading the contents fails.

        """
        if not url.isEmpty():
            text = cls.load_data(url, encoding)
        d = cls(url, encoding)
        if not url.isEmpty():
            d.setPlainText(text)
            d.setModified(False)
            d.loaded()
            app.documentLoaded(d)
        return d

    def __init__(self, url=None, encoding=None):
        """Create a new Document with url and encoding.

        Does not load the contents, you should use load() for that, or
        use the new_from_url() constructor to instantiate a new Document
        with the contents loaded.

        """
        if url is None:
            url = QUrl()
        super(Document, self).__init__()
        self.setDocumentLayout(QPlainTextDocumentLayout(self))
        self._encoding = encoding
        self._url = url # avoid urlChanged on init
        self.setUrl(url)
        self.modificationChanged.connect(self.slotModificationChanged)
        app.documents.append(self)
        app.documentCreated(self)

    def slotModificationChanged(self):
        app.documentModificationChanged(self)

    def close(self):
        self.closed()
        app.documentClosed(self)
        app.documents.remove(self)

    def load(self, url=None, encoding=None, keepUndo=False):
        """Load the specified or current url (if None was specified).

        Currently only local files are supported. An IOError is raised
        when trying to load a nonlocal URL.

        If loading succeeds and an url was specified, the url is make the
        current url (by calling setUrl() internally).

        If keepUndo is True, the loading can be undone (with Ctrl-Z).

        """
        if url is None:
            url = QUrl()
        u = url if not url.isEmpty() else self.url()
        text = self.load_data(u, encoding or self._encoding)
        if keepUndo:
            c = QTextCursor(self)
            c.select(QTextCursor.Document)
            c.insertText(text)
        else:
            self.setPlainText(text)
        self.setModified(False)
        if not url.isEmpty():
            self.setUrl(url)
        self.loaded()
        app.documentLoaded(self)

    def save(self, url=None, encoding=None):
        """Saves the document to the specified or current url.

        Currently only local files are supported. An IOError is raised
        when trying to save a nonlocal URL.

        If saving succeeds and an url was specified, the url is made the
        current url (by calling setUrl() internally).

        """
        if url is None:
            url = QUrl()
        u = url if not url.isEmpty() else self.url()
        filename = u.toLocalFile()
        # currently, we do not support non-local files
        if not filename:
            raise IOError("not a local file")
        # keep the url if specified when we didn't have one, even if saving
        # would fail
        if self.url().isEmpty() and not url.isEmpty():
            self.setUrl(url)
        with self.saving(), app.documentSaving(self):
            with open(filename, "wb") as f:
                f.write(self.encodedText())
                f.flush()
                os.fsync(f.fileno())
            self.setModified(False)
            if not url.isEmpty():
                self.setUrl(url)
        self.saved()
        app.documentSaved(self)

    def url(self):
        return self._url

    def setUrl(self, url):
        """ Change the url for this document. """
        if url is None:
            url = QUrl()
        old, self._url = self._url, url
        changed = old != url
        # number for nameless documents
        if self._url.isEmpty():
            nums = [0]
            nums.extend(doc._num for doc in app.documents if doc is not self)
            self._num = max(nums) + 1
        else:
            self._num = 0
        if changed:
            self.urlChanged(url, old)
            app.documentUrlChanged(self, url, old)

    def encoding(self):
        return variables.get(self, "coding") or self._encoding

    def setEncoding(self, encoding):
        self._encoding = encoding

    def encodedText(self):
        """Return the text of the document as a bytes string encoded in the
        correct encoding.

        The line separator is '\\n' on Unix/Linux/Mac OS X, '\\r\\n' on Windows.

        Useful to save to a file.

        """
        text = util.platform_newlines(self.toPlainText())
        return util.encode(text, self.encoding())

    def documentName(self):
        """Return a suitable name for this document.

        This is only to be used for display. If the url of the document is
        empty, something like "Untitled" or "Untitled (3)" is returned.

        """
        if self._url.isEmpty():
            if self._num == 1:
                return _("Untitled")
            else:
                return _("Untitled ({num})").format(num=self._num)
        else:
            return os.path.basename(self._url.path())


