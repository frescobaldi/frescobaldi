# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2019 by Wilbert Berendsen
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
Code to load and manage PDF documents to view.
"""

import itertools

from PyQt6.QtCore import QSettings

try:
    import popplerqt5
except ImportError:
    popplerqt5 = None

import app
import plugin
import resultfiles
import signals
import pagedview


# This signal gets emitted when a finished Job has created new PDF document(s).
documentUpdated = signals.Signal() # Document


@app.jobFinished.connect
def _on_job_finished(document, job):
    if group(document).update():
        documentUpdated(document, job)


def group(document):
    """Returns a DocumentGroup instance for the given text document."""
    return DocumentGroup.instance(document)


class DocumentGroup(plugin.DocumentPlugin):
    """Represents a group of PDF documents, created by the text document it belongs to.

    Multiple MusicView instances can use this group, they can store the positions
    of the Documents in the viewer themselves via a weak-key dictionary on the Document
    instances returned by documents(). On update() these Document instances will be reused.

    The global documentUpdated(Document) signal will be emitted when the global
    app.jobFinished() signal causes a reload of documents in a group.

    """
    def __init__(self, document):
        self._documents = None
        document.loaded.connect(self.update, -100)

    def documents(self):
        """Returns the list of PDF Document objects created by our text document."""
        # If the list is asked for the very first time, update
        if self._documents is None:
            self._documents = []
            self.update()
        return self._documents[:]

    def update(self, newer=None):
        """Queries the resultfiles of this text document for PDF files and loads them.

        Returns True if new documents were loaded.
        If newer is True, only PDF files newer than the source document are returned.
        If newer is False, all PDF files are returned.
        If newer is None (default), the setting from the configuration is used.

        """
        if newer is None:
            newer = QSettings().value("musicview/newer_files_only", True, bool)

        results = resultfiles.results(self.document())
        files = results.files(".pdf", newer)
        if files:
            # reuse the older Document objects, they will probably be displaying
            # (about) the same documents, and so the viewer will remember their position.
            documents = []
            for filename, doc in zip(files, itertools.chain(
                    self._documents or (), itertools.repeat(None))):
                if doc:
                    doc.setSource(filename)
                else:
                    doc = pagedview.loadPdf(filename)
                doc.updated = newer or results.is_newer(filename)
                documents.append(doc)
            self._documents = documents
            return True

    def clear(self):
        """'Forgets' the list of PDF documents."""
        if self._documents:
            self._documents.clear()

