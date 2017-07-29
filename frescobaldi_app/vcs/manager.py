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

from PyQt5.QtCore import QObject

from . import gitrepo
from .helper import GitHelper, HgHelper, SvnHelper

class VCSManager(QObject):

    def __init__(self):
        self._doc_view_map = {}
        self._git_repo_manager = gitrepo.RepoManager()
        self._hg_repo_manager  = None
        self._svn_repo_manager = None

    def setCurrentDocument(self, view):
        self._doc_view_map[view.document()] = view
        doc_url = view.document().url()
        if doc_url.isEmpty():
            return
        root_path, relative_path = GitHelper.extract_git_path(doc_url.path())
        if root_path:
            self._git_repo_manager.track_document(view, root_path,
                                                    relative_path)
            return
        root_path, relative_path = HgHelper.extract_hg_path(doc_url.path())
        if root_path:
            # TODO: Add hg support
            return
        root_path, relative_path = SvnHelper.extract_svn_path(doc_url.path())
        if root_path:
            # TODO: Add svn support
            return

    def slotDocumentClosed(self, doc):
        if doc.url().isEmpty():
            return
        root_path, relative_path = GitHelper.extract_git_path(doc.url().path())
        if root_path:
            self._git_repo_manager.untrack_document(root_path, relative_path)
            return
        root_path, relative_path = HgHelper.extract_hg_path(doc.url().path())
        if root_path:
            # TODO: Add hg support
            return
        root_path, relative_path = SvnHelper.extract_svn_path(doc.url().path())
        if root_path:
            # TODO: Add svn support
            return

    def slotDocumentUrlChanged(self, doc, url, old):
        if not old.isEmpty():
            root_path, relative_path = GitHelper.extract_git_path(old.path())
            if root_path:
                self._git_repo_manager.untrack_document(root_path,
                                                        relative_path)
                return
            root_path, relative_path = HgHelper.extract_hg_path(old.path())
            if root_path:
                # TODO: Add hg support
                return
            root_path, relative_path = SvnHelper.extract_svn_path(old.path())
            if root_path:
                # TODO: Add svn support
                return

        root_path, relative_path = GitHelper.extract_git_path(url.path())
        if root_path:
            self._git_repo_manager.track_document(self._doc_view_map[doc],
                                                    root_path,
                                                    relative_path)
            return
        root_path, relative_path = HgHelper.extract_hg_path(url.path())
        if root_path:
            # TODO: Add hg support
            return
        root_path, relative_path = SvnHelper.extract_svn_path(url.path())
        if root_path:
            # TODO: Add svn support
            return

