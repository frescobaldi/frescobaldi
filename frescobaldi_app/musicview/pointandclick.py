# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Handles Point and Click.
"""

from __future__ import unicode_literals

import re
import os
import sys
import weakref

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QTextCursor

import qpopplerview

import app
import util
import scratchdir
import ly.lex
import tokeniter
import percentcoding


# cache point and click handlers for poppler documents
_cache = weakref.WeakKeyDictionary()

# parse textedit urls
textedit_match = re.compile(r"^textedit://(.*?):(\d+):(\d+)(?::\d+)$").match


# Make sure that also on Windows, directory slashes remain forward
if os.name == 'nt':
	def normpath(path):
		return os.path.normpath(path).replace('\\', '/')
else:
	normpath = os.path.normpath


def readfilename(match):
    """Returns the filename from the match object resulting from textedit_match."""
    fname = match.group(1)
    lat1 = fname.encode('latin1')
    try:
        lat1 = percentcoding.decode(lat1)
    except ValueError:
        pass
    try:
        fname = lat1.decode(sys.getfilesystemencoding())
    except UnicodeError:
        pass
    # normalize path (although this might change a path if it contains
    # symlinks followed by '/../' !
    fname = normpath(fname)
    return fname


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
        self._docs = {}
        
        import popplerqt4
        with qpopplerview.lock(document):
            for num in range(document.numPages()):
                page = document.page(num)
                for link in page.links():
                    if isinstance(link, popplerqt4.Poppler.LinkBrowse):
                        m = textedit_match(link.url())
                        if m:
                            filename, line, col = readurl(m)
                            l = self._links.setdefault(filename, {})
                            l.setdefault((line, col), []).append((num, link.linkArea()))

        for filename in self._links:
            for d in app.documents:
                s = scratchdir.scratchdir(d)
                if (s.directory() and util.equal_paths(filename, s.path())
                    or d.url().toLocalFile() == filename):
                    self.bind(filename, d)
        app.documentLoaded.connect(self.slotDocumentLoaded)
        app.documentClosed.connect(self.slotDocumentClosed)
    
    def bind(self, filename, doc):
        """Binds the given filename to the given document.
        
        When the document disappears, the binding is removed automatically.
        While a document is bound, textedit links are stored as QTextCursors,
        so they keep their position even if the user changes the document.
        
        """
        if filename not in self._docs:
            self._docs[filename] = BoundLinks(doc, self._links[filename])
    
    def slotDocumentLoaded(self, doc):
        """Called when a new document is loaded, it maybe possible to bind to it."""
        filename = doc.url().toLocalFile()
        if filename in self._links:
            self.bind(filename, doc)
    
    def slotDocumentClosed(self, doc):
        """Called when a document is closed, removes the bound links."""
        for filename, b in self._docs.items():
            if b.document == doc:
                break
        else:
            return
        del self._docs[filename]
    
    def cursor(self, link, load=False):
        """Returns the destination of a link as a QTextCursor of the destination document.
        
        If load (defaulting to False) is True, the document is loaded if it is not yet loaded.
        Returns None if the url was not valid or the document could not be loaded.
        
        """
        import popplerqt4
        if not isinstance(link, popplerqt4.Poppler.LinkBrowse) or not link.url():
            return
        m = textedit_match(link.url())
        if m:
            filename, line, col = readurl(m)
            bound = self._docs.get(filename)
            if bound:
                return bound.cursor(line, col)
            elif load and os.path.isfile(filename):
                # this also calls bind(), via app.documentLoaded
                app.openUrl(QUrl.fromLocalFile(filename))
                bound = self._docs.get(filename)
                if bound:
                    return bound.cursor(line, col)
    
    def boundLinks(self, doc):
        """Returns the Bound links object for the given text document."""
        for b in self._docs.values():
            if b.document == doc:
                return b


class BoundLinks(object):
    """Stores links as QTextCursors for a document."""
    def __init__(self, doc, links):
        """Creates QTextCursor instances for every link, keeps a reference to the document."""
        self.document = doc
        # make a sorted list of cursors with their [(pageNum, linkArea) ...] destinations list
        self._cursor_dict = d = {}              # mapping from (line, col) to QTextCursor
        self._cursors = cursors = []            # sorted list of the cursors
        self._destinations = destinations = []  # corresponding list of destinations
        for pos, dest in sorted(links.items()):
            line, column = pos
            b = doc.findBlockByNumber(line - 1)
            if b.isValid():
                c = d[pos] = QTextCursor(doc)
                c.setPosition(b.position() + column)
                cursors.append(c)
                destinations.append(dest)
        
    def cursor(self, line, column):
        """Returns the QTextCursor for the give line/col."""
        return self._cursor_dict.get((line, column))
    
    def cursors(self):
        """Returns the list of cursors, sorted on cursor position."""
        return self._cursors
        
    def destinations(self):
        """Returns the list of destinations.
        
        Each destination corresponds with the cursor at the same index in the cursors() list.
        Each destination is a list of (pageNum, QRectF) pairs, because many point-and-click
        objects can point to the same place in the text document.
        
        """
        return self._destinations
    
    def indices(self, cursor):
        """Returns a Python slice object or None or False.
        
        If a slice, it specifies the range of destinations (in the destinations() list)
        that the given QTextCursor points to. The cursor must of course belong to our document.
        
        If None or False, it means that there is no object in the cursors neighbourhood.
        If False, it means that it is e.g. preferred to clear earlier highlighted objects.
        
        This method performs quite a bit trickery: it also returns the destination when a cursor
        points to the _ending_ point of a slur, beam or phrasing slur.
        
        """
        cursors = self._cursors
        
        def findlink(pos):
            # binary search in list of cursors
            lo, hi = 0, len(cursors)
            while lo < hi:
                mid = (lo + hi) // 2
                if pos < cursors[mid].position():
                    hi = mid
                else:
                    lo = mid + 1
            return lo - 1
        
        if cursor.hasSelection():
            end = findlink(cursor.selectionEnd() - 1)
            if end >= 0:
                start = findlink(cursor.selectionStart())
                if start < 0 or cursors[start].position() < cursor.selectionStart():
                    start += 1
                if start <= end:
                    return slice(start, end+1)
            return False
            
        index = findlink(cursor.position())
        if index < 0:
            return # before all other links
        
        cur2 = cursors[index]
        if cur2.position() < cursor.position():
            # is the cursor at an ending token like a slur end?
            prevcol = -1
            if cur2.block() == cursor.block():
                prevcol = cur2.position() - cur2.block().position()
            col = cursor.position() - cursor.block().position()
            found = False
            tokens = tokeniter.Runner(cursor.block(), True)
            for token in tokens.backward_line():
                if token.pos <= prevcol:
                    break
                elif token.pos <= col:
                    if isinstance(token, ly.lex.MatchEnd) and token.matchname in (
                            'slur', 'phrasingslur', 'beam'):
                        # YES! now go backwards to find the opening token
                        nest = 1
                        name = token.matchname
                        for token in tokens.backward():
                            if isinstance(token, ly.lex.MatchStart) and token.matchname == name:
                                nest -= 1
                                if nest == 0:
                                    found = True
                                    break
                            elif isinstance(token, ly.lex.MatchEnd) and token.matchname == name:
                                nest += 1
                        break
            if found:
                index = findlink(tokens.block.position() + token.pos)
                if index < 0 or cursors[index].block() != tokens.block:
                    return
            elif cur2.block() != cursor.block():
                return False
        # highlight it!
        return slice(index, index+1)


