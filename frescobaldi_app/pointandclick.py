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
Generic Point and Click handling.
"""


import os
import collections

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QTextCursor

import app
import scratchdir
import ly.lex.lilypond
import ly.document
import lydocument


class Links(object):
    """Stores point and click links grouped by filename."""
    def __init__(self):
        self._links = collections.defaultdict(lambda: collections.defaultdict(list))
        self._docs = {}

    def add_link(self, filename, line, column, destination):
        """Add a link.

        filename, line and column, describe the position in the source file.

        destination can be any object that describes where the link points to.

        """
        self._links[filename][(line, column)].append(destination)

    def finish(self):
        """Call this when you are done with adding links.

        This method tries to bind() already loaded documents and starts
        monitoring document open/close events.

        You can also use the links as a context manager and then add links.
        On exit, finish() is automatically called.

        """
        for filename in self._links:
            d = scratchdir.findDocument(filename)
            if d:
                self.bind(filename, d)
        app.documentLoaded.connect(self.slotDocumentLoaded)
        app.documentClosed.connect(self.slotDocumentClosed)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.finish()

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

    def cursor(self, filename, line, column, load=False):
        """Returns the destination of a link as a QTextCursor of the destination document.

        If load (defaulting to False) is True, the document is loaded if it is not yet loaded.
        Returns None if the document could not be loaded.

        """
        bound = self._docs.get(filename)
        if bound:
            return bound.cursor(line, column)
        elif load and os.path.isfile(filename):
            # this also calls bind(), via app.documentLoaded
            app.openUrl(QUrl.fromLocalFile(filename))
            bound = self._docs.get(filename)
            if bound:
                return bound.cursor(line, column)

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
        # make a sorted list of cursors with their [destination, ...] destinations list
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
        """Return the list of cursors, sorted on cursor position."""
        return self._cursors

    def destinations(self):
        """Return the list of destination lists.

        Each destination corresponds with the cursor at the same index in
        the cursors() list. Each destination is a list of destination items
        that were originally added using Links.add_link, because many
        point-and-click objects can point to the same place in the text
        document.

        """
        return self._destinations

    def indices(self, cursor):
        """Return a Python slice object or None or False.

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
            tokens = ly.document.Runner(lydocument.Document(cursor.document()))
            tokens.move_to_block(cursor.block(), True)
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


def positions(cursor):
    """Return a list of QTextCursors describing the grob the cursor points at.

    When the cursor point at e.g. a slur, the returned cursors describe both
    ends of the slur.

    The returned list may contain zero to two cursors.

    """
    c = lydocument.cursor(cursor)
    c.end = None
    source = lydocument.Source(c, True)
    for token in source.tokens:
        break
    else:
        return []

    cur = source.cursor(token, end=0)
    cursors = [cur]

    # some heuristic to find the relevant range(s) the linked grob represents
    if isinstance(token, ly.lex.lilypond.Direction):
        # a _, - or ^ is found; find the next token
        for token in source:
            if not isinstance(token, (ly.lex.Space, ly.lex.Comment)):
                break
    end = token.end + source.block.position()
    if token == '\\markup':
        # find the end of the markup expression
        depth = source.state.depth()
        for token in source:
            if source.state.depth() < depth:
                end = token.end + source.block.position()
                break
    elif token == '"':
        if isinstance(token, ly.lex.StringEnd):
            # a bug in LilyPond can cause the texedit url to point at the
            # closing quote of a string, rather than the starting quote
            end = token.end + source.block.position()
            r = lydocument.Runner.at(c, False, True)
            for token in r.backward():
                if isinstance(token, ly.lex.StringStart):
                    cur.setPosition(token.pos)
                    break
        else:
            # find the end of the string
            for token in source:
                if isinstance(token, ly.lex.StringEnd):
                    end = token.end + source.block.position()
                    break
    elif isinstance(token, ly.lex.MatchStart):
        # find the end of slur, beam. ligature, phrasing slur, etc.
        name = token.matchname
        nest = 1
        for token in source:
            if isinstance(token, ly.lex.MatchEnd) and token.matchname == name:
                nest -= 1
                if nest == 0:
                    cursors.append(source.cursor(token))
                    break
            elif isinstance(token, ly.lex.MatchStart) and token.matchname == name:
                nest += 1

    cur.setPosition(end, QTextCursor.KeepAnchor)
    return cursors

