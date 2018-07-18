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
VCS interface (application and documents)
"""

from abc import ABCMeta, abstractmethod

import os

from PyQt5.QtCore import QObject


class Repo(QObject):
    """
    Interface for classes managing VCS repositories.
    Currently we only support Git, but this level of
    abstraction is intended to offer an interface to
    add other VCS comparably easily.
    """
    __metaclass__ = ABCMeta

    _job_class = None
    _queue_class = None
    
    def __init__(self, root):
        super(Repo, self).__init__()
        self._jobqueue = self._queue_class()
        self._root_path = root
        self._documents = {}

    def _error_handler(self, func_name, error_msg):
        """
        Show a warning message and disable tracking.
        """
        import vcs
        vcs.VCS.error(self, func_name, error_msg)
        self.disable()

    @abstractmethod
    def branches(self, local=True):
        """
        Returns a string list of branch names.
        If local is False also return 'remote' branches.
        """
        pass

    @abstractmethod
    def checkout(self, branch):
        pass

    @abstractmethod
    def current_branch(self):
        """
        Returns the name of the current branch.
        """
        pass

    @abstractmethod
    def has_branch(self, branch):
        """
        Returns True if the given branch exists.
        Checks by actually running git branch.
        """
        pass

    @abstractmethod
    def has_remote(self, remote):
        """Returns True if the given remote name is registered."""
        pass

    @abstractmethod
    def has_remote_branch(self, branch):
        """
        Return True if the given branch
        is tracking a remote branch.
        """
        pass

    @abstractmethod
    def remotes(self):
        """Return a string list with registered remote names"""
        pass

    @abstractmethod
    def tracked_remote(self, branch):
        """
        Return a tuple with the remote and branch tracked by
        the given branch.
        In most cases both values will be identical, but a branch
        can also track a differently named remote branch.
        Return ('local', 'local') if it doesn't track any branch.
        """
        pass

    @abstractmethod
    def tracked_remote_label(self, branch):
        """
        Return a string to be used for remote branch info.
        Either 'local', the remote name or remote/branch.
        """
        pass

    # ####################
    # Public API functions
    def disable(self):
        """Disable tracking"""
        try: self.repoChanged.disconnect()
        except Exception: pass
        try: self._repoChangeDetected.disconnect()
        except Exception: pass
        try: self._watcher.fileChanged.disconnect()
        except Exception: pass
        for relative_path in self._documents:
            self._documents[relative_path].disable()

    def track_document(self, vcs_doc):
        """
        Attach a document tracker to the corresponding view
        and add it to the list of tracked documents in the current
        repository.
        """
        path = vcs_doc.url().path()
        if path in self._documents:
            return
        self._documents[path] = vcs_doc
        view = vcs_doc.view()
        view.viewSpace().connectVcsLabels(view)

    def untrack_document(self, path):
        """
        Remove the document tracker from the corresponding view.
        """
        if path not in self._documents:
            return
        tracked_doc = self._documents.pop(path)
        view = tracked_doc.view()
        try:
            # If this is called from the VCS error _error_handler
            # the connections may not have been made yet
            # so we ignore an expected failure
            view.viewSpace().disconnectVcsLabels(view)
        except TypeError:
            pass
        view.set_vcs_document(None)
        view.set_vcs_repository(None)
        tracked_doc.deleteLater()

    def corresponding_view(self, relative_path):
        """
        Return the view that holds a document with the given relative
        path, or None if no such document is tracked.
        """
        #TODO: Consider if we need this for untracked documents
        # in a repository as well
        return self._documents.get(relative_path, None).view()

    def root(self):
        """
        Return the absolute path to the root of the repository.
        """
        return self._root_path

    def name(self):
        """
        Return the name (directory name) of the repository.
        """
        _, name = os.path.split(self._root_path)
        return name


class RepoManager(QObject):
    """Manages all repositories of a given VCS type."""
    
    _repo_class = None
    
    def __init__(self):
        super(RepoManager, self).__init__()
        self._repos = {}

    def repo(self, vcs_doc):
        root_path = vcs_doc.root()
        if root_path not in self._repos:
            self._repos[root_path] = self._repo_class(root_path)
        return self._repos[root_path]

    def track_document(self, vcs_doc):
        repo = self.repo(vcs_doc)
        repo.track_document(vcs_doc)
        return repo
