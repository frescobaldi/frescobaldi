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
Manage a Git repository
"""


import sys
import os
import re
from functools import partial

from PyQt5.QtCore import QProcess, QFileSystemWatcher, pyqtSignal, QObject

import app
from . import abstractrepo, gitjob, gitdoc

class GitError(Exception):
    pass

class Repo(abstractrepo.Repo):
    """
    Manage a git repository, be it
    the running Frescobaldi application
    or a document's project.
    """
    repoChanged = pyqtSignal()
    _repoChangeDetected = pyqtSignal()

    _document_class = gitdoc.Document
    _queue_class = gitjob.JobQueue
    
    def __init__(self, root):
        super().__init__(root)
        self._remotes = []
        self._local_branches = []
        self._remote_branches = []
        self._tracked_remotes = {}
        self._set_repo_changed_signals()
        self._update_all_attributes(blocking=True)
        self._repoChangeDetected.connect(self._update_all_attributes)
        self.repoChanged.connect(self._broadcast_changed_signal)

    def _error_handler(self, func_name, error_msg):
        repo_name = self.name()
        if type(error_msg) is not str:
            error_msg = gitjob.Job.error(error_msg)
        print("Git Error occurred during running "+ func_name + " in repo "
                    + repo_name + "\n" + error_msg)
        self.disable()

    def _set_repo_changed_signals(self):
        """
        Sets a QFileSystemWatcher object to monitor this repo.

        Explanation:
            We are monitoring the ".git/index" file here.
            Git operations like 'pull', 'merge', 'checkout', 'stage' and
            'commit' all update the index file in .git folder.
            Each operation only updates the index once. While '.git' folder
            will be updated three times during a 'commit' command. So index file
            is a good marker.

        """
        self._watcher = QFileSystemWatcher()
        self._index_path = os.path.join(self._root_path, '.git', 'index')
        self._watcher.addPath(self._index_path)
        self._watcher.fileChanged.connect(self._emit_repo_changed_signal)

    def _emit_repo_changed_signal(self, path):
        """
        Emits repoChanged signal and resets the file-watcher.
        """
        self._repoChangeDetected.emit()
        self._watcher.removePath(self._index_path)
        self._watcher.addPath(self._index_path)

    def _update_branches(self, blocking=False):
        """
        Updates self._branches and self._current_branch. Then you can access
        them through branches(), current_branch()

        Args:
            local(bool): If local is False, it also fetch 'remote' branches.
            blocking(bool): If blocking is True, this function will run
                synchronously

        """
        def result_parser(gitprocess, exitcode):
            if exitcode == 0:
                self._local_branches = []
                self._remote_branches = []
                result_lines = gitprocess.stdout()
                for line in result_lines:
                    branch = line.strip()
                    if branch.startswith('* '):
                        branch = branch.lstrip('* ')
                        self._current_branch = branch
                    if branch.endswith('.stgit'):
                        continue
                    if branch.startswith('remotes'):
                        self._remote_branches.append(branch)
                    else:
                        self._local_branches.append(branch)
                gitprocess.executed.emit(0)
            else:
                error_handler(str(gitprocess.stderr(isbinary = True), 'utf-8'))

        args = ['branch', '--color=never', '-a']
        git = gitjob.Job(self.root())
        git.preset_args = args
        error_handler = partial(self._error_handler, '_update_branches')
        git.errorOccurred.connect(error_handler)
        git.finished.connect(result_parser)
        if blocking == True:
            git.run_blocking()
        else:
            self._jobqueue.enqueue(git)

    def _update_tracked_remote_name(self, branch, blocking = False):
        def get_remote_name(gitprocess, exitcode):
            if gitprocess.stderr():
                error_handler(str(gitprocess.stderr(isbinary = True), 'utf-8'))
            if exitcode == 0:
                if not branch in self._tracked_remotes:
                    self._tracked_remotes[branch] = {}
                remote_name = gitprocess.stdout()
                self._tracked_remotes[branch]['remote_name'] = remote_name[0]
            else:
                if not branch in self._tracked_remotes:
                    self._tracked_remotes[branch] = {}
                self._tracked_remotes[branch]['remote_name'] = 'local'
            gitprocess.executed.emit(0)

        args = ["config", "branch." + branch + ".remote"]
        git = gitjob.Job(self.root())
        git.preset_args = args
        error_handler = partial(self._error_handler, '_update_tracked_remote_name')
        git.errorOccurred.connect(error_handler)
        git.finished.connect(get_remote_name)
        if blocking == True:
            git.run_blocking()
        else:
            self._jobqueue.enqueue(git)

    def _update_tracked_remote_branches(self, blocking = False):
        def get_remote_branches(gitprocess, exitcode):
            if exitcode == 0:
                result_lines = gitprocess.stdout()
                for line in result_lines:
                    line = line.strip()
                    if line.startswith('* '):
                        line = line.lstrip('* ')
                    hunks = line.split()
                    local_branch = hunks[0]
                    if hunks[2].startswith('['):
                        remote_name = self._tracked_remotes[local_branch]['remote_name']
                        start_pos = len(remote_name) + 2
                        colon_ind = hunks[2].find(':')
                        end_pos = colon_ind if colon_ind > -1 else len(hunks[2])-1
                        self._tracked_remotes[local_branch]['remote_branch'] = hunks[2][start_pos:end_pos]
                    else:
                        if not local_branch in self._tracked_remotes:
                            self._tracked_remotes[local_branch] = {}
                        self._tracked_remotes[local_branch]['remote_branch'] = 'local'
                self.repoChanged.emit()
                gitprocess.executed.emit(0)
            else:
                error_handler(str(gitprocess.stderr(isbinary = True), 'utf-8'))

        args = ["branch", "-vv"]
        git = gitjob.Job(self.root())
        git.preset_args = args
        error_handler = partial(self._error_handler, '_update_tracked_remote_branches')
        git.errorOccurred.connect(error_handler)
        git.finished.connect(get_remote_branches)
        if blocking == True:
            git.run_blocking()
        else:
            self._jobqueue.enqueue(git)


    def _update_tracked_remotes(self, blocking = False):
        self._tracked_remotes = {}
        for local_branch in self._local_branches:
            self._update_tracked_remote_name(local_branch, blocking = blocking)
        self._update_tracked_remote_branches(blocking = blocking)

    def _update_remotes(self, blocking = False):
        def get_remote_names(gitprocess, exitcode):
            if exitcode == 0:
                self._remotes = gitprocess.stdout()
                gitprocess.executed.emit(0)
            else:
                error_handler(str(gitprocess.stderr(isbinary = True), 'utf-8'))

        args = ["remote", "show"]
        git = gitjob.Job(self.root())
        git.preset_args = args
        error_handler = partial(self._error_handler, '_update_tracked_remotes')
        git.errorOccurred.connect(error_handler)
        git.finished.connect(get_remote_names)
        if blocking == True:
            git.run_blocking()
        else:
            self._jobqueue.enqueue(git)

    def _update_all_attributes(self, blocking = False):
        self._update_branches(blocking = blocking)
        self._update_remotes(blocking = blocking)
        self._update_tracked_remotes(blocking = blocking)

    def _broadcast_changed_signal(self):
        for relative_path in self._documents:
            self._documents[relative_path].update(repoChanged = True)

    # ####################
    # Public API functions

    def branches(self, local=True):
        """
        Returns a string list of branch names.
        If local is False also return 'remote' branches.
        """
        res = []
        res.extend(self._local_branches)
        if not local:
            res.extend(self._remote_branches)
        return res

    def checkout(self, branch):
        """
        Tries to checkout a branch.
        May raise a GitError exception
        """
        def success_tracker(gitprocess, exitcode):
            nonlocal succeed
            nonlocal err_msg
            if exitcode == 0:
                succeed = True
            else:
                succeed = False
                err_msg = str(gitprocess.stderr(isbinary = True), 'utf-8')

        def error_tracker(errcode):
            nonlocal succeed
            nonlocal err_msg
            succeed = False
            err_msg = 'Error: ' + gitjob.Job.error(errcode)

        args = ["checkout", "-q", branch]
        git = gitjob.Job(self.root())
        git.preset_args = args
        git.errorOccurred.connect(error_tracker)
        git.finished.connect(success_tracker)
        succeed = True
        err_msg = None
        git.run_blocking()
        if not succeed:
            raise GitError(err_msg)

    def current_branch(self):
        """
        Returns the name of the current branch.
        """
        return self._current_branch

    def has_branch(self, branch):
        """
        Returns True if the given local branch exists.
        """
        return (branch in self._local_branches)

    def has_remote(self, remote):
        """Returns True if the given remote name is registered."""
        return remote in self.remotes()

    def has_remote_branch(self, branch):
        """
        Return True if the given branch is tracking a remote branch.
        """
        remote, remote_branch = self.tracked_remote(branch)
        return (remote != "local" or remote_branch != "local")

    def remotes(self):
        """Return a string list with registered remote names"""
        return self._remotes

    def tracked_remote(self, branch):
        """
        Return a tuple with the remote and branch tracked by
        the given branch.
        In most cases both values will be identical, but a branch
        can also track a differently named remote branch.
        Return ('local', 'local') if it doesn't track any branch.
        """
        if not self.has_branch(branch):
            raise GitError('Branch not found: ' + branch)
        return (self._tracked_remotes[branch]['remote_name'], self._tracked_remotes[branch]['remote_branch'])

    def tracked_remote_label(self, branch):
        """
        Returns a label for the tracked branch to be used in the GUI.
        Consists of one of
        - 'local'
        - the remote name
        - remote name concatenated with the remote branch
          (if it should differ from the local branch name).
        """
        remote, remote_branch = self.tracked_remote(branch)
        if remote == 'local':
            return 'local'
        if branch == remote_branch:
            return remote
        else:
            return remote + '/' + remote_branch

class RepoManager(abstractrepo.RepoManager):
    """Class managing all Git repositories."""
    
    _repo_class = Repo
    
    def __init__(self):
        super().__init__()
