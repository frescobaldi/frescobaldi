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
Manages the history of the open documents of a MainWindow.
Contains smart logic to switch documents if the active document is closed.

If no documents remain, listen to other HistoryManager instances and
make the document set-current there also current here.
"""

import weakref

import app
import signals

# This signal is emitted whenever a MainWindow sets a document current (active)
# Any HistoryManager can listen to it and follow it if no document is current
_setCurrentDocument = signals.Signal()  # Document


class HistoryManager(object):
    """Keeps the history of document switches by the user.

    If a document is closed, the previously active document is set active.
    If no documents remain, nothing is done.

    """
    def __init__(self, mainwindow, othermanager=None):
        self.mainwindow = weakref.ref(mainwindow)
        self._documents = list(othermanager._documents if othermanager else app.documents)
        self._has_current = bool(self._documents)
        mainwindow.currentDocumentChanged.connect(self.setCurrentDocument)
        app.documentCreated.connect(self.addDocument, 1)
        app.documentClosed.connect(self.removeDocument, 1)
        _setCurrentDocument.connect(self._listen)

    def addDocument(self, doc):
        self._documents.insert(-1, doc)

    def removeDocument(self, doc):
        active = doc is self._documents[-1]
        if active:
            if len(self._documents) > 1:
                self.mainwindow().setCurrentDocument(self._documents[-2])
            else:
                # last document removed; listen to setCurrentDocument from others
                self._has_current = False
        self._documents.remove(doc)

    def setCurrentDocument(self, doc):
        self._documents.remove(doc)
        self._documents.append(doc)
        self._has_current = True
        # notify possible interested parties
        _setCurrentDocument(doc)

    def documents(self):
        """Returns the documents in order of most recent been active."""
        return self._documents[::-1]

    def _listen(self, document):
        """Called when any MainWindow emits the currentDocumentChanged."""
        if not self._has_current:
            # prevent nested emits of this signal from reacting MainWindows
            with _setCurrentDocument.blocked():
                self.mainwindow().setCurrentDocument(document)


