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
Handles Point and Click.
"""

import re
import weakref

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QTextCursor

import popplerqt4
import qpopplerview

import app
import scratchdir


# cache point and click handlers for poppler documents
_cache = weakref.WeakKeyDictionary()

# parse textedit urls
textedit_match = re.compile(r"^textedit://(.*?):(\d+):(\d+)(?::\d+)$").match


def readfilename(match):
    """Returns the filename from the match object resulting from textedit_match."""
    return QUrl.fromPercentEncoding(match.group(1))


def readurl(match):
    """Returns filename, line, col for the match object resulting from textedit_match."""
    return readfilename(match), int(match.group(2)), int(match.group(3))


def links(document):
    try:
        return _cache[document]
    except KeyError:
        l = _cache[document] = Links(document)
        return l


class Links(object):
    """Stores all the links of a Poppler document sorted by URL and text position.
    
    Only textedit:// urls are stored.
    
    """
    def __init__(self, document):
        self._links = {}
        self._docs = weakref.WeakValueDictionary()
        
        qpopplerview.cache.wait(document)
        for num in range(document.numPages()):
            page = document.page(num)
            for link in page.links():
                if isinstance(link, popplerqt4.Poppler.LinkBrowse):
                    m = textedit_match(link.url())
                    if m:
                        filename, line, col = readurl(m)
                        l = self._links.setdefault(filename, {})
                        l.setdefault((line, col), []).append((page, link.linkArea()))

        for filename in self._links:
            for d in app.documents:
                if (scratchdir.scratchdir(d).path() == filename
                    or d.url().toLocalFile() == filename):
                    self.bind(filename, d)
        app.documentLoaded.connect(self.slotDocumentLoaded)
    
    def bind(self, filename, doc):
        """Binds the given filename to the given document.
        
        When the document disappears, the binding is removed automatically.
        While a document is bound, textedit links are stored as QTextCursors,
        to they keep their position even if the user changes the document.
        
        """
        self._docs[filename] = BoundLinks(doc, self._links[filename])
    
    def slotDocumentLoaded(self, doc):
        """Called when a new document is loaded, it maybe possible to bind to it."""
        filename = doc.url().toLocalFile()
        if filename in self._links and filename not in self._docs:
            self.bind(filename, doc)
    
    def cursor(self, link, load=False):
        """Returns the destination of a link as a QTextCursor of the destination document).
        
        If load (defaulting to False) is True, the document is loaded if it is not yet loaded.
        Returns None if the url was not valid or the document could not be loaded.
        
        """
        m = textedit_match(link.url())
        if m:
            filename, line, col = readurl(m)
            bound = self._docs.get(filename)
            if bound:
                return bound.cursor(line, col)
            elif load:
                # this also calls bind(), via app.documentLoaded
                app.openUrl(QUrl.fromLocalFile(filename))
                bound = self._docs.get(filename)
                if bound:
                    return bound.cursor(line, col)


class BoundLinks(object):
    """Stores links as QTextCursors for a document."""
    _bound_links_instances = []
    
    def __init__(self, doc, links):
        self._document = weakref.ref(doc, self.remove)
        self._bound_links_instances.append(self)
        
        # make a sorted list of cursors with their [(page, linkArea) ...] list
        self._cursors = cursors = {}
        for pos, dest in links.items():
            line, column = pos
            b = doc.findBlockByNumber(line - 1)
            if b.isValid():
                c = QTextCursor(doc)
                c.setPosition(b.position() + column)
                cursors[pos] = (c, dest)
    
    def cursor(self, line, column):
        """Returns the QTextCursor for the give line/col."""
        return self._cursors[(line, column)][0]
        
    def remove(self, wr):
        self._bound_links_instances.remove(self)



