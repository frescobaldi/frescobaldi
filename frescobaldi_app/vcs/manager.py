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

import os

from PyQt5.QtCore import QObject

from . import gitrepo, gitdoc, VCS

class VCSManager(QObject):
    """
    The VCSManager is a single object (child of mainwindow)
    managing all (document) VCS versioning resources.
    """

    def __init__(self):
        # map vcs_documents to their view
        self._doc_views = {}
        # map vcs_documents to their Repo instance.
        self._doc_trackers = {}

    def setCurrentDocument(self, view):
        """Called from mainwindow after a view has been (newly) created."""
        url = view.document().url()
        if url.isEmpty():
            # keep a reference for use in slotDocumentUrlChanged()
            self._empty_view = view
            return
        else:
            self._empty_view = None
        
        # store a reference from the (editor) document to the view
        self._doc_views[url.path()] = view
        
        vcs_type, vcs_document = VCS.instantiate_doc(url, view)
        if not (vcs_document and vcs_document.is_tracked()):
            # The document is not in a repository or it is not tracked
            return
        
        repo_manager = VCS.repo_manager(vcs_type)
        repo = repo_manager.track_document(vcs_document)
        # store a pointer to the repo object that manages the document
        self._doc_trackers[url.path()] = repo

    def slotDocumentClosed(self, doc):
        """Called from mainwindow after a view has been closed."""
        url = doc.url()
        if url.isEmpty():
            return
        repo = self._doc_trackers.get(url.path(), None)
        if repo:
            # repo is None if the closed document hasn't been tracked
            repo.untrack_document(url.path())

    def slotDocumentUrlChanged(self, doc, url, old):
        """
        Called from mainwindow after the Url for the current document has changed.
        This happens
        a) when a document is loaded into the empty first view or
        b) when a document is saved with a new name ("Save as...")
        'doc' is the new document.Document() instance
        """
        
        # reference to the view that has changed
        view = self._doc_views[old.path()] if old.path() else self._empty_view
        
        # determine if the old document has been tracked and untrack it if applicable
        repo = self._doc_trackers.get(old.path(), None)
        if repo:
            repo.untrack_document(old.path())
        
        # handle the new document in the view
        self.setCurrentDocument(view)
        
        view.viewSpace().viewChanged.emit(view)
