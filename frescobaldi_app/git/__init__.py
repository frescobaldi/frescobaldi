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
        Parse the repository's config file.
        TODO: This only parses branches and remotes so far.
        If we need more we have to implement this here.
        """
        
        def read_sections(lines, search_term, dict_key):
            """Parse the file, looking for only one type of entries."""
            for i in range(len(lines)):
                line = lines[i]
                if line.startswith('[' + search_term  + ' "'):
                    name = line[line.find('"')+1:line.rfind('"')]
                    dk = self.config[dict_key][name] = {}
                    i += 1
                    while i < len(lines):
                        if len(lines[i]) == 0:
                           i += 1
                           continue
                        if lines[i][0] != '[':
                            # add key/value pairs to the dictionary.
                            # Note that this is agnostic to the pairs,
                            # so it isn't known which keys are present.
                            key, value = self._key_value(lines[i])
                            dk[key] = value
                        i += 1

        # The Git object can only be instantiated with a valid repo.
        # So we can assume .git/config to be present 
        fin = open(os.path.join(self.rootDir, '.git', 'config'))
        lines = fin.read().split('\n')
        
        # reset config dictionary
        self.config = {}
        self.config['branches'] = {}
        self.config['remotes'] = {}
        
        #read definitions
        read_sections(lines, 'branch', 'branches')
        read_sections(lines, 'remote', 'remotes')
        
    def _run_git_command(self, cmd, args = []): 
        """
        run a git command and return its output
        as a string list.
        Raise an exception if it returns an error.
        - cmd is the git command (without 'git')
        - args is a string or a list of strings
        """
        cmd = ['git', cmd]
        if type(args) == str:
            cmd.append(args)
        else:
            cmd.extend(args)
        pr = subprocess.Popen(' '.join(cmd), cwd = self.rootDir, 
                              shell = True, 
                              stdout = subprocess.PIPE, 
                              stderr = subprocess.PIPE)
        (out, error) = pr.communicate()
        if error:
            raise Exception(str(error))
        result = str(out).split('\n')
        if result[-1] == '':
            result.pop()
        return result

    # ####################
    # Public API functions

    def branches(self, local=True):
        """
        Return a string list of branch names.
        The currently checked out branch will have a
        leading '* '.
        If local == False also return 'remote' branches.
        """
        args = [] if local else ['-a']
        return [line.strip() for line in self._run_git_command('branch', args)]
        
    def current_branch(self, remote = False):
        """
        return the name of the current branch.
        If remote == True prepend the name of the 
        tracked remote).
        """
        branch_list = self._run_git_command('branch')
        for branch in branch_list:
            if branch[0] == '*':
                branch = branch[2:]
                remote_name = ''
                if remote:
                    remote_name = self.tracked_remote(branch)
                    remote_name = ' [' + remote_name + ']' if remote_name else ' [local]'
                return branch + remote_name
        raise Exception('No branch found')

    def has_branch(self, branch):
        return branch in self.config['branches']
    
    def has_remote(self, remote):
        return remote in self.config['remotes']
        
    def tracked_remote(self, branch):
        """
        Return the name of the remote tracked by the given branch.
        Return '' if it doesn't track any branch.
        NOTE: This assumes that the remote branch is named 
        the same as the local one.
        """
        if not self.has_branch(branch):
            raise Exception('Branch not found: ' + branch)
        if 'remote' in self.config['branches'][branch]:
            return self.config['branches'][branch]['remote']
        else:
            return ''
        
# instantiate the git.app object for managing the application
app = Git(os.path.join(sys.path[0], '..'))
