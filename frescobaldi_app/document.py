# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
from PyQt4.QtGui import QPlainTextDocumentLayout, QTextDocument

import app
import view
import util
import highlighter
import textformats
import variables
import signals


class Document(QTextDocument):
    
    urlChanged = signals.Signal()
    closed = signals.Signal()
    loaded = signals.Signal()
    saved = signals.Signal()
    
    def __init__(self, url=None, encoding=None):
        super(Document, self).__init__()
        self._materialized = False
        self._encoding = encoding
        self._url = url # avoid urlChanged on init
        self.setUrl(url)
        self.modificationChanged.connect(self.slotModificationChanged)
        app.documents.append(self)
        app.documentCreated(self)
        self.load()
        
    def slotModificationChanged(self):
        app.documentModificationChanged(self)

    def close(self):
        app.documents.remove(self)
        self.closed()
        app.documentClosed(self)

    def load(self):
        """Loads the current url.
        
        Returns True if loading succeeded, False if an error occurred,
        and None when the current url is empty or non-local.
        Currently only local files are supported.
        
        """
        fileName = self.url().toLocalFile()
        if fileName:
            try:
                with open(fileName) as f:
                    data = f.read()
            except (IOError, OSError):
                return False # errors are caught in MainWindow.openUrl()
            
            self.setPlainText(util.decode(data))
            self.setModified(False)
            self.loaded()
            app.documentLoaded(self)
            return True
            
    def save(self):
        """Saves the document to the current url.
        
        Returns True if saving succeeded, False if an error occurred,
        and None when the current url is empty or non-local.
        Currently only local files are supported.
        
        """
        fileName = self.url().toLocalFile()
        if fileName:
            try:
                with open(fileName, "w") as f:
                    f.write(self.encodedText())
            except (IOError, OSError):
                return False
            self.setModified(False)
            self.saved()
            return True

    def createView(self):
        """Returns a new View on our document."""
        if not self._materialized:
            self.setDocumentLayout(QPlainTextDocumentLayout(self))
            self.highlighter = highlighter.Highlighter(self)
            self._materialized = True
        return view.View(self)
    
    def url(self):
        return self._url
        
    def setUrl(self, url):
        """ Change the url for this document. """
        changed = self._url != url
        self._url = url or QUrl()
        # number for nameless documents
        if self._url.isEmpty():
            nums = [0]
            nums.extend(doc._num for doc in app.documents if doc is not self)
            self._num = max(nums) + 1
        else:
            self._num = 0
        if changed:
            self.urlChanged()
            app.documentUrlChanged(self)
    
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
    
    def htmlCopy(self, type='editor'):
        """Returns a new QTextDocument with highlighting set as HTML textcharformats.
        
        type can be 'editor' (the default) or 'printer'.
        
        """
        data = textformats.formatData(type)
        return highlighter.htmlCopy(self, data)


