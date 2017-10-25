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

import vcs
from . import gitrepo, gitdoc
from .helper import GitHelper, HgHelper, SvnHelper

class VCSManager(QObject):

    def __init__(self):
        self._doc_views = {}
        self._doc_trackers = {}
        self._vcs_data = {
            'git': {
                'repo_manager': gitrepo.RepoManager(),
                'meta_directory': '.git',
                'document_class': gitdoc.Document
            },
            'hg': {
                'repo_manager': None,
                'meta_directory': '.hg',
                'document_class': None
            },
            'svn': {
                'repo_manager': None,
                'meta_directory': 'unsupported',
                'document_class': None
            }
        }
        self._git_repo_manager = gitrepo.RepoManager()
        self._hg_repo_manager  = None
        self._svn_repo_manager = None

    def repo_root_type(self, path):
        """Check if path points to the root of a VCS repository.
        Return the name of the VCS if found, otherwise False."""
        if not os.path.isdir(path):
            return False
        for vcs in self._vcs_data:
            if os.path.exists(os.path.join(path, self._vcs_data[vcs]['meta_directory'])):
                return vcs
        return False

    def vcs_path_info(self, full_path):
        """
        Determine if path represents a file in the working tree of a supported
        VCS repository.
        Return a tuple of vcs_type, repository_root, relative_path.
        Otherwise return a 'None' 3-tuple.
        """

        # ensure there is no trailing slash
        sep = os.path.altsep if os.path.altsep else ''
        sep += os.path.sep
        path = full_path.rstrip(sep)

        # We are only interested in writable files,
        # write-protected files can't be versioned anyway
        if os.access(full_path, os.F_OK | os.W_OK):

            # We are working on paths only and know that path represents a file.
            path = os.path.split(path)[0]

            root_name = os.path.abspath(os.sep)
            while path != root_name:
                vcs_type = self.repo_root_type(path)
                if vcs_type:
                    return (vcs_type, path,          # TODO: is this replace necessary?
                            os.path.relpath(full_path, path).replace('\\', '/'))
                path = os.path.split(path)[0]

        return (None, None, None)

    def instantiate(self, url, view):
        """
        Test if the given url represents a document in a repository.
        Return either an instance of the corresponding document class or (None, None).
        """
        vcs_type, root_path, relative_path = self.vcs_path_info(url.path())
        
        if not vcs_type:
            return (None, None)
        
        return (vcs_type, self._vcs_data[vcs_type]['document_class'](root_path, relative_path, view))

    def setCurrentDocument(self, view):
        """Called from mainwindow after a view has been (newly) created."""
        url = view.document().url()
        if url.isEmpty():
            self._empty_view = view
            return
        else:
            self._empty_view = None
        
        # store a reference from the (editor) document to the view
        self._doc_views[url.path()] = view
        
        vcs_type, vcs_document = self.instantiate(url, view)
        if not (vcs_document and vcs_document.is_tracked()):
            # The document is not in a repository or it is not tracked
            return
        
        repo_manager = self._vcs_data[vcs_type]['repo_manager']
        repo = repo_manager.track_document(vcs_document)
        # store a pointer to the repo object that manages the document
        self._doc_trackers[url.path()] = repo

    def slotDocumentClosed(self, doc):
        url = doc.url()
        if url.isEmpty():
            return
        repo = self._doc_trackers.get(url.path(), None)
        if repo:
            repo.untrack_document(url.path())

    def slotDocumentUrlChanged(self, doc, url, old):
        view = self._doc_views[old.path()] if old.path() else self._empty_view
        old_tracked = repo = self._doc_trackers.get(old.path(), None)
        if old_tracked:
            repo.untrack_document(old.path())
        
        self.setCurrentDocument(view)
        new_tracked = self._doc_trackers.get(url.path(), None)
        
        # TODO: Is this the right way to get to the ViewSpace?
        view_space = view.parentWidget().parentWidget()
        view_space.viewChanged.emit(view)

        if not old_tracked and new_tracked:
            view_space.connectVcsLabels(view)
        
        if old_tracked and not new_tracked:
            view_space.disconnectVcsLabels(view)

