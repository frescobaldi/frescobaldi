# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Git interface (application and documents)
"""

from __future__ import unicode_literals

import sys
import os
import subprocess

import app
import info

class GitError(Exception):
    pass
    
class Git(object):
    """
    Manage a git repository, be it
    the running Frescobaldi application
    or a document's project.
    """
    def __init__(self, root):
        if not os.path.isdir(root):
            raise Exception(_("The given directory '{rootdir} "
                              "doesn't seem to be a Git repository.".format(rootdir=root)))
        self.rootDir = root
        self._read_config()
    
    # #########################
    # Internal helper functions
    
    def _key_value(self, line):
        """
        Return a tuple with the key and value parts of a
        .git/config section entry.
        """
        line = line.strip()
        sep = line.find('=')
        return (line[:sep-1], line[sep+2:])
        
    def _read_config(self):
        """
        Produce a hierarchical dictionary representing the
        .git/config file.
        Currently we will only use the 'branch' and 'remote'
        dictionaries:
        - self.config['branch']
        - self.config['remote']
        """
        
        # The Git object can only be instantiated with a valid repo.
        # So we can assume .git/config to be present 
        fin = open(os.path.join(self.rootDir, '.git', 'config'))
        lines = fin.read().split('\n')
        
        # reset config dictionary
        cf = self.config = {}
        # target will be the (sub-)dictionary to add keys to
        target = {}
        # parse file
        for line in lines:
            if line == '' or line.strip().startswith('#'):
                continue
            elif line.startswith('['):
                # add new section
                items = line.strip('[').strip(']').split()
                if not items[0] in cf:
                    cf[items[0]] = {}
                target = cf[items[0]]
                if len(items) > 1:
                    name = items[1].strip('"')
                    if not name in target:
                        target[name] = {}
                    target = target[name]
            else:
                # add new key-value pair
                key, value = self._key_value(line)
                target[key] = value        
        return
                
    def _run_git_command(self, cmd, args = []): 
        """
        run a git command and return its output
        as a string list.
        Raise an exception if it returns an error.
        - cmd is the git command (without 'git')
        - args is a string or a list of strings
        """
        cmd = ['git', cmd]
        if isinstance(args, str) or isinstance(args, unicode):
            cmd.append(args)
        else:
            cmd.extend(args)
        pr = subprocess.Popen(' '.join(cmd), cwd = self.rootDir, 
                              shell = True, 
                              stdout = subprocess.PIPE, 
                              stderr = subprocess.PIPE)
        (out, error) = pr.communicate()
        if error:
            raise GitError(str(error))
        result = str(out).split('\n')
        if result[-1] == '':
            result.pop()
        return result

    # ####################
    # Public API functions

    def branches(self, local=True):
        """
        Returns a string list of branch names.
        The currently checked out branch will have a
        leading '* '.
        If local == False also return 'remote' branches.
        """
        args = [] if local else ['-a']
        return [line.strip() for line in self._run_git_command('branch', args)]
        
    def checkout(self, branch):
        print 'enter checkout()'
        self._run_git_command('checkout', branch)
        
    def current_branch(self):
        """
        Returns the name of the current branch.
        """
        for branch in self.branches():
            if branch[0] == '*':
                return branch[2:]
        raise GitError('current_branch: No branch found')

    def has_branch(self, branch):
        """
        Returns True if the given branch exists.
        Checks by actually running git branch.
        """
        for br in self.branches():
            if br.strip('* ') == branch :
                return True 
        return False
    
    def has_remote(self, remote):
        """Returns True if the given remote name is registered."""
        return remote in self.config['remote']
        
    def has_remote_branch(self, branch):
        """
        Return True if the given branch
        is tracking a remote branch.
        Checks if the branch is present in .git/config
        """
        return branch in self.config['branch']
        
    def remotes(self):
        """Return a string list with registered remote names"""
        return self._run_git_command('remote show')
        
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
        if self.has_remote_branch(branch):
            remote_name = self.config['branch'][branch]['remote']
            remote_merge = self.config['branch'][branch]['merge']
            remote_branch = remote_merge[remote_merge.rfind('/')+1:]
            return (remote_name, remote_branch)
        else:
            return ('local', 'local')

class GitApp(Git):
    def __init__(self):
        super(GitApp, self).__init__(os.path.join(sys.path[0], '..'))
    
    def upstream_remote(self):
        """
        Returns the name of the official
        upstream remote or '' in case this shouldn't be registered
        (e.g. one runs from a fork)
        """
        for remote in self.remotes():
            if info.upstream_repository in self.config['remote'][remote]['url']:
                return remote
        return ''
