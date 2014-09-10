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
A Frescobaldi (LilyPond) document.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QPlainTextDocumentLayout, QTextCursor, QTextDocument

import app
import util
import variables
import signals


class Document(QTextDocument):
    
    urlChanged = signals.Signal() # new url, old url
    closed = signals.Signal()
    loaded = signals.Signal()
    saved = signals.Signal()
    
    @classmethod
    def load_data(cls, url, encoding=None):
        """Class method to load document contents from an url.
        
        This is intended to open a document without instantiating one
        if loading the contents fails.
        
        This method returns the text contents of the url as decoded text,
        thus a unicode string.
        
        """
        filename = url.toLocalFile()
        
        # currently, we do not support non-local files
        if not filename:
            raise IOError("not a local file")
        with open(filename) as f:
            data = f.read()
        return util.decode(data, encoding)
    
    @classmethod
    def new_from_url(cls, url, encoding=None):
        """Create and return a new document, loaded from url.
        
        This is intended to open a new Document without instantiating one
        if loading the contents fails.
        
        """
        text = cls.load_data(url, encoding)
        d = cls(url, encoding)
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
        with app.documentSaving(self):
            with open(filename, "w") as f:
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
        """Returns the text of the document encoded in the correct encoding.
        
        Useful to save to a file.
        
        """
        try:
            return self.toPlainText().encode(self.encoding() or 'utf-8')
        except (UnicodeError, LookupError):
            return self.toPlainText().encode('utf-8')
        
    def documentName(self):
        """ Returns a suitable name for this document. """
        if self._url.isEmpty():
            if self._num == 1:
                return _("Untitled")
            else:
                return _("Untitled ({num})").format(num=self._num)
        else:
            return os.path.basename(self._url.path())


