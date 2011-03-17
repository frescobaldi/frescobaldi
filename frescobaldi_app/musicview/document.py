# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Code to load and manage PDF documents to view.
"""


import itertools
import os
import weakref

from PyQt4.QtCore import QByteArray

import popplerqt4

import app
import plugin
import resultfiles
import signals


_cache = weakref.WeakValueDictionary()



def load(filename):
    """Returns a Poppler.Document for the given filename, caching it (weakly)."""
    mtime = os.path.getmtime(filename)
    key = (mtime, filename)
    
    try:
        return _cache[key]
    except KeyError:
        with open(filename, 'rb') as f:
            data = QByteArray(f.read())
        doc = _cache[key] = popplerqt4.Poppler.Document.loadFromData(data)
        return doc


class Document(object):
    """Represents a (lazily) loaded PDF document and retains its position in the viewer.
    
    The position can be set by simply writing/reading the position attribute.
    
    """
    def __init__(self):
        self._filename = None
        self._dirty = True
        self.position = 0, 0.5, 0 # see qpopplerview.View.position()
        
    def filename(self):
        return self._filename
    
    def setFilename(self, filename):
        """Sets a filename.
        
        The document will be reloaded if the filename changed,
        or if the mtime of the document has changed.
        
        """
        self._filename = filename
        self._dirty = True
            
    def document(self):
        """Returns the PDF document the filename points to, reloading if the filename was set."""
        if self._dirty:
            self._document = load(self._filename)
            self._dirty = False
        return self._document


class DocumentGroup(plugin.DocumentPlugin):
    """Represents a group of PDF documents, created by the text document it belongs to.
    
    One of the documents is the current document, displayed in the viewer.
    
    """
    
    # reloaded() is emitted when the documents have been updated,
    # the current index may then also have been changed.
    reloaded = signals.Signal()
    
    # emitted when the current document is changed via setCurrentIndex()
    currentIndexChanged = signals.Signal() # int
    
    def __init__(self, document):
        self._documents = []
        self._current = 0
        
    def documents(self):
        """Returns the list of PDF Document objects created by our text document.
        
        update() must have been called before calling this.
        
        """
        return self._documents[:]
    
    def update(self):
        """Queries the resultfiles of this text document for PDF files and loads them.
        
        emits the reloaded() signal if there were any documents.
        
        """
        files = resultfiles.results(self.document()).files(".pdf")
        if files:
            # reuse the older Document objects, they will probably be displaying
            # (about) the same documents, and so they will retain their position
            # in the viewer.
            def docs():
                # yield existing docs and then new ones
                for d in self._documents:
                    yield d
                while True:
                    yield Document()
            documents = []
            for filename, doc in zip(files, docs()):
                doc.setFilename(filename)
                documents.append(doc)
            self._documents = documents
            if self._current >= len(files):
                self._current = 0
            self.reloaded()

    def setCurrentIndex(self, index):
        """Changes the current document and emits the currentIndexChanged(int) signal."""
        if index < len(self._documents) and index != self._current:
            self._current = index
            self.currentIndexChanged(index)
    
    def currentIndex(self):
        """Returns the index of the current document in the list returned by documents()."""
        return self._current



@app.jobFinished.connect
def _update_documents(document):
    DocumentGroup.instance(document).update()


