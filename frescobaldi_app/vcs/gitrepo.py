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
import subprocess

from .abstractrepo import AbstractVCSRepo

class GitError(Exception):
    pass

class Repo(AbstractVCSRepo):
    """
    Manage a git repository, be it
    the running Frescobaldi application
    or a document's project.
    """

    _git_available = None

    def __init__(self, root):
        if not os.path.isdir(os.path.join(root, '.git')):
            raise GitError(_("The given directory '{rootdir} "
                             "doesn't seem to be a Git repository.".format(rootdir=root)))
        self.rootDir = root

    @classmethod
    def run_command(cls, cmd, args=[], dir=None):
        """
        run a git command and return its output
        as a string list.
        Raise an exception if it returns an error.
        - cmd is the git command (without 'git')
        - args is a string or a list of strings
        If no dir is passed the running dir of
        Frescobaldi is used as default
        """
        dir = os.path.normpath(os.path.join(sys.path[0], '..')) if dir is None else dir
        from PyQt5.QtCore import QSettings
        s = QSettings()
        s.beginGroup("helper_applications")
        git_cmd = s.value("git", "git", str)
        git_cmd = git_cmd if git_cmd else "git"
        cmd = [git_cmd, cmd]
        cmd.extend(args)
        pr = subprocess.Popen(cmd, cwd=dir,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True)
        (out, error) = pr.communicate()
        if error:
            raise GitError(error)
        result = out.split('\n')
        if result[-1] == '':
            result.pop()
        return result


    @classmethod
    def vcs_available(cls):
        """Return True if Git is installed on the system"""
        if cls._git_available is None:
            try:
                cls.run_command('--version')
                cls._git_available = True
            except (GitError):
                cls._git_available = False
        return cls._git_available

    # #########################
    # Internal helper functions

    def _run_command(self, cmd, args=[]):
        """
        run a git command and return its output
        as a string list.
        Raise an exception if it returns an error.
        - cmd is the git command (without 'git')
        - args is a string or a list of strings
        """
        return Repo.run_command(cmd, args, self.rootDir)

    def _branches(self, local=True):
        """
        Returns a tuple.
        The first element is the list of branch names.
        The second element is the name of the current branch (may be None).
        If local is False also return 'remote' branches.
        """
        args = ['--color=never']
        if not local:
            args.append('-a')

        branches = []
        current_branch = None
        for line in self._run_command('branch', args):
            branch = line.strip()
            if branch.startswith('* '):
                branch = branch.lstrip('* ')
                current_branch = branch
            if branch.endswith('.stgit'):
                continue
            branches.append(branch)

        return (branches, current_branch)

    # ####################
    # Public API functions

    def branches(self, local=True):
        """
        Returns a string list of branch names.
        If local is False also return 'remote' branches.
        """
        return self._branches(local)[0]

    def checkout(self, branch):
        """
        Tries to checkout a branch.
        Add '-q' option because git checkout will
        return its confirmation message on stderr.
        May raise a GitError exception"""
        self._run_command('checkout', ['-q', branch])

    def current_branch(self):
        """
        Returns the name of the current branch.
        """
        current_branch = self._branches(local=True)[1]
        if not current_branch:
            raise GitError('current_branch: No branch found')
        return current_branch

    def has_branch(self, branch):
        """
        Returns True if the given local branch exists.
        """
        return (branch in self.branches(local=True))

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
        return self._run_command('remote', ['show'])

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

        remote_name = self._run_command("config",
                                            ["branch." + branch + ".remote"])
        remote_merge = self._run_command("config",
                                             ["branch." + branch + ".merge"])
        if not remote_name or not remote_merge:
            return ('local', 'local')

        remote_name = remote_name[0]
        remote_merge = remote_merge[0]
        remote_branch = remote_merge[remote_merge.rfind('/')+1:]
        return (remote_name, remote_branch)

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
