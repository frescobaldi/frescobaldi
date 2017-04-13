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
This module checks if documents are changed on disk.

The documentChangedOnDisk(Document) signal is emitted once when a document is
changed on the disk.  The 'changed' attribute of the Document's DocumentWatcher
instance is set to True.  Saving or reloading a Document sets the 'changed'
flag back to False.

Use start() to start the document watcher, and stop() to stop it if desired.

"""


import contextlib
import os

from PyQt5.QtCore import QFileSystemWatcher, QUrl

import app
import plugin
import signals


__all__ = ['documentChangedOnDisk', 'DocumentWatcher', 'start', 'stop']


documentChangedOnDisk = signals.Signal() # Document


# one global QFileSystemWatcher instance
watcher = None


class DocumentWatcher(plugin.DocumentPlugin):
    """Maintains if a change was detected for a document."""
    def __init__(self, d):
        self.changed = False

    def isdeleted(self):
        """Return True if some change has occurred, the document has a local
        filename, but the file is not existing on disk.

        """
        if self.changed:
            filename = self.document().url().toLocalFile()
            if filename:
                return not os.path.isfile(filename)
        return False


def addUrl(url):
    """Add a url (QUrl) to the filesystem watcher."""
    filename = url.toLocalFile()
    if filename and filename not in watcher.files():
        watcher.addPath(filename)


def removeUrl(url):
    """Remove a url (QUrl) from the filesystem watcher."""
    filename = url.toLocalFile()
    if filename:
        watcher.removePath(filename)


def unchange(document):
    """Mark document as not changed (anymore)."""
    DocumentWatcher.instance(document).changed = False


def documentUrlChanged(document, url, old):
    """Called whenever the URL of an existing Document changes."""
    for d in app.documents:
        if d.url() == old:
            break
    else:
        removeUrl(old)
    addUrl(url)


def documentClosed(document):
    """Called whenever a document closes."""
    for d in app.documents:
        if d is not document and d.url() == document.url():
            return
    removeUrl(document.url())


def documentLoaded(document):
    """Called whenever a document loads."""
    addUrl(document.url())


@contextlib.contextmanager
def whileSaving(document):
    """Temporarily suppress the watching of the document during a code block."""
    try:
        removeUrl(document.url())
        yield
    finally:
        addUrl(document.url())


def fileChanged(filename):
    """Called whenever the global filesystem watcher detects a change."""
    url = QUrl.fromLocalFile(filename)
    doc = app.findDocument(url)
    if doc:
        w = DocumentWatcher.instance(doc)
        if not w.changed:
            w.changed = True
            documentChangedOnDisk(doc)


def start():
    """Start the document watcher."""
    global watcher
    if watcher is None:
        watcher = QFileSystemWatcher()
        app.documentLoaded.connect(documentLoaded)
        app.documentUrlChanged.connect(documentUrlChanged)
        app.documentClosed.connect(documentClosed)
        app.documentSaving.connect(whileSaving)
        watcher.fileChanged.connect(fileChanged)
        for d in app.documents:
            documentLoaded(d)


def stop():
    """Stop the document watcher."""
    global watcher
    if watcher is not None:
        watcher.fileChanged.disconnect(fileChanged)
        watcher.removePaths(watcher.files())
        app.documentLoaded.disconnect(documentLoaded)
        app.documentUrlChanged.disconnect(documentUrlChanged)
        app.documentClosed.disconnect(documentClosed)
        app.documentSaving.disconnect(whileSaving)
        watcher.deleteLater()
        watcher = None


# always-on connections
app.documentLoaded.connect(unchange)
app.documentSaved.connect(unchange)
app.documentUrlChanged.connect(unchange)
