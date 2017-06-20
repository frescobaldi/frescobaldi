# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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

import os
import re
import gitjob
import tempfile

from PyQt5.QtCore import pyqtSignal


class Repo():
    """
    """
    ############################################################################
    # features
    # 1.  whether the working directory is a git repo
    # 2.  extract HEAD, Index and working file and save them to tmp files
    # 3.  update HEAD, Index, working temp files
    # 4.  run git diff command between temp files and get output
    # 5.  parse git diff output
    # 6.  current_branch() 
    # 7.  branches()
    # 8.  checkout()
    # 9.  has_branch()
    # 10. has_remote() 
    # 11. has_remote_branch()
    # 12. remotes()
    # 13. tracked_remote()
    # 14. tracked_remote_label()
    # 15. set_working_directory()
    # 16. whether the file is an untracked file
    # 17. whether the file is an ignored file
    # 18. whether git has been installed 
    # 19. use which git
    # 19. get git version
    ############################################################################ 

    def __init__(self, current_view = None):
        self.is_repository = False
        # self.target_is_file makes sense only when self.isRepository is True
        # True when given path is a file path
        # False when given path is a folder path
        self.target_is_file = False
        # update signal emits signal when git content updates
        self._update_signal = pyqtSignal(bool)
        # git command instance
        self._git = gitjob.Git()
        # Identifier of comparison object
        # 'Index' for Index
        # 'HEAD' for HEAD 
        # commit-hash for specific commit
        self._compare_against = 'HEAD'
        # root path of current working directory
        self._root_path = None
        # current file/directory's relative path
        self._relative_path = None
        self._temp_committed_file = None 
        self._temp_index_file = None
        self._temp_working_file = None  
        # current file's view instance
        # None: If the instance is not operating on a file
        self._current_view = current_view
        # cache git diff result 
        self._git_diff_cache = ''
    
    def __del__(self):
        """Caller is responsible for clean up the temp files"""
        if self._temp_committed_file:
            os.unlink(self._temp_committed_file)
        if self._temp_index_file:
            os.unlink(self._temp_index_file)
        if self._temp_working_file:
            os.unlink(self._temp_working_file)

    def set_working_directory(self, path):
        """
        Set the variables:
            self._root_path,  self._relative_path, self.is_repository, 
            self.target_is_file
        
        Arguments:
            path: path can be a folder's absolute path or a file's absolute path

        Returns:
            True: given path locates in a git repository
            False: case 1. given path is not a valid path  
                   case 2. given path does not locate in a git repository 
        """
        def is_git_path(path):
            """
            Return True if 'path' is a valid git working tree.
            """
            return path and os.path.exists(os.path.join(path, '.git'))
    

        def get_work_path(ori_path):
            """
            If the giving ori_path is git initialized. 
            Split the ori_path into the working tree part and relative path part.
            This function handles both file pathes and directory pathes.

            Note:
                This is a local alternative to calling the git command:

                    git rev-parse --show-toplevel

            Arguments:
                ori_path (string): a absolute path.

            Returns:
                (root path of the working proj, relative path)
                (None, None) for non-git-initilized file_path
            """

            # ensure there is no trailing slash
            sep = os.path.altsep if os.path.altsep else ''
            sep += os.path.sep
            ori_path = ori_path.rstrip(sep)
            if ori_path and os.path.exists(ori_path):
                if os.path.isdir(ori_path):
                    _, name = os.path.split(ori_path)
                    path = ori_path
                else:
                    path, name = os.path.split(ori_path)    
                
                # files within '.git' path are not part of a work tree
                while path and name and name != '.git':
                    if is_git_path(path):
                        return (path, os.path.relpath(
                            ori_path, path).replace('\\', '/'))
                    path, name = os.path.split(path)
            
            return (None, None)


        self._root_path, self._relative_path = get_work_path(path)
        
        if self._root_path:
            # set the git command's working environment
            self._git.setWorkingDirectory(self._root_path)
            self.is_repository = True
            self.target_is_file = not os.path.isdir(path)
            
        return self._root_path != None 
    
    def _branches(self, local=True):
        """
        Returns a list of branch names

        Arguments:
            local: If local is False also return 'remote' branches.

        Returns: 
            Returns a tuple.
            The first element is the list of branch names.
            The second element is the name of the current branch (may be None).
        """
        args = ['branch', '--color=never']
        if not local:
            args.append('-a')

        branches = []
        current_branch = None
        for line in self._git.run_blocking(args):
            branch = line.strip()
            if branch.startswith('* '):
                branch = branch.lstrip('* ')
                current_branch = branch
            if branch.endswith('.stgit'):
                continue
            branches.append(branch)

        return (branches, current_branch)

    def _create_tmp_file(self, dir = None, prefix = 'Frescobaldi_git_tmp_'):
        """
        Creates a new tmp file and return the path to it. 

        CAUTION: Caller is responsible for clean up
        
        Arguments:
            dir: If dir is specified, the file will be created in that directory,
                 otherwise, a default directory is used. 
            prefix: the prefix of new created tmp file

        Returns:
            Return a absolute pathname to the new tmp file.     
        """
        file, filepath = tempfile.mkstemp(prefix = prefix, dir = dir)
        os.close(file)
        return filepath    

    def _read_Index_file(self):
        """
        Returns content of the current file's corresponding file in Index.
        
        Reference of using [tree-ish]:[relative_path] in argments list:
            https://stackoverflow.com/questions/4044368/what-does-tree-ish-mean-in-git
            https://www.kernel.org/pub/software/scm/git/docs/gitrevisions.html#_specifying_revisions
        """
        args = [
           'cat-file',
            # smudge filters are supported with git 2.11.0+ only
            '--filters' if self._git.version() >= (2, 11, 0) else '-p',
            ':'+self._relative_path
        ]
        return self._git.run_blocking(args, isbinary = True)

    def _read_committed_file(self, commit):
        """
        Read the content of the file from specific commit

        Reference of using [tree-ish]:[relative_path] in argments list:
            https://stackoverflow.com/questions/4044368/what-does-tree-ish-mean-in-git
            https://www.kernel.org/pub/software/scm/git/docs/gitrevisions.html#_specifying_revisions

        Arguments:
            commit: the identifier of the commit to read file from
                    E.g.  'HEAD', 'origin/master', hash id of a commit

        Returns:
            content of current's file's corresponding file in the inputed commit
        """    
        args = [
           'cat-file',
            # smudge filters are supported with git 2.11.0+ only
            '--filters' if self._git.version() >= (2, 11, 0) else '-p',
            commit + ':'+self._relative_path
        ]
        return self._git.run_blocking(args, isbinary = True)

    def _update_temp_committed_file(self):
        """
        Update committed temp file from the commit: self._compare_against
        
        ? Should we unify all the line endings here
        ? Exception handling is left to be implemented
        """
        content = self._read_committed_file(self._compare_against)
        if content:
            # Unify all the line endings
            # contents = contents.replace(b'\r\n', b'\n')
            # contents = contents.replace(b'\r', b'\n')
            # Create temp file
            if not self._temp_committed_file:
                self._temp_committed_file = self._create_tmp_file()
            # Write content to temp file
            with open(self._temp_committed_file, 'wb') as file:
                file.write(content)
    
    def _update_temp_index_file(self):
        """
        ? Should we unify all the line endings here
        ? Exception handling is left to be implemented
        """
        content = self._read_Index_file()
        if content:
            # Unify all the line endings
            # contents = contents.replace(b'\r\n', b'\n')
            # contents = contents.replace(b'\r', b'\n')
            # Create temp file
            if not self._temp_index_file:
                self._temp_index_file = self._create_tmp_file()
            # Write content to temp file
            with open(self._temp_index_file, 'wb') as file:
                file.write(content)

    def _update_temp_working_file(self):
        """
        Save the current file to a temp file for diff compare
        """
        if not self._temp_working_file:
                self._temp_working_file = self._create_tmp_file()
        content = self._current_view.document().encodedText()
        with open(self._temp_working_file, 'wb') as file:
                file.write(content)    
    
    def _run_diff(self, original, current):
        """
        Run git diff command between two files

        Arguments:
            original: absolute path string of the original file
            current:  absolute path string of the current file
            
        Note:
            original, current nedd not locate in a git repo

        Return:
            Binary output of the git diff command         
   
        ? Whiteblocks handling:  wait to be implemented
        ? Whether using 'patience' git diff algorithm
          I found this: http://bramcohen.livejournal.com/73318.html
          Need further investigation into it.
        """
        # '-U0' to generate diffs without context code (actually 0 line) 
        # '--no-index' to generate diffs between two files outside the git repo
        args = ['diff', '-U0', '--no-color', '--no-index', original, current]
        binary_result  = self._git.run_blocking(args, isbinary = True)
        self._git_diff_cache = str(binary_result, 'utf-8')
    
    def file_status(self):
        """
        Check a file's git status. 
        The result is organized in a tuple. The first element is the status of 
        the file in Index, the second element is the status of the working file.
        The information in a tuple is designed to be displayed in bottom border 
        of the editor. e.g.
        1. Tuple: ('newly added', 'modified') 
           Info:  newly added in Index, modified
        2. Tuple: ('staged', '')
           Info:  staged in Index
        3. Tuple: ('staged', 'modified')
           Info:   staged in Index, modified
        4. Tuple: ('', 'untracked')
           Info:   untracked

        Git command: 'git status --porcelain --ignored [RELATIVE_PATH]' 
        returns many different statuses.  We only need part of them here. 
        """
        # only works in a repository and the given path should be a file path
        if not self.is_repository or not self.target_is_file:
            return ('', '')
       
        # arguments to get file status
        status_args = ['status', '--porcelain', '--ignored', self._relative_path]
        
        output_strs = self._git.run_blocking(status_args)
        
        status_dict = {
            'A ' : ('newly added', ''),
            'AM' : ('newly added', 'modified'),
            'AD' : ('newly added', 'deleted'),
            'M ' : ('staged', ''),
            'MM' : ('staged', 'modified'),
            'MD' : ('staged', 'deleted'),
            '??' : ('', 'untracked'),
            '!!' : ('', 'ignored'),
        }
        if not output_strs:
            return ('', 'committed')
        try:
            return status_dict[output_strs[0][:2]]
        except KeyError:
            # return ('', '') when receive a status not listed in status_dict
            return ('', '')

    def extract_linenum_diff(self):
        """
        Parse unified diff with 0 lines of context.

        Hunk range info format:
          @@ -3,2 +4,0 @@
            Hunk originally starting at line 3, and occupying 2 lines, now
            starts at line 4, and occupies 0 lines, i.e. it was deleted.
          @@ -9 +10,2 @@
            Hunk size can be omitted, and defaults to one line.

        Dealing with ambiguous hunks:
          "A\nB\n" -> "C\n"
          Was 'A' modified, and 'B' deleted? Or 'B' modified, 'A' deleted?
          Or both deleted? To minimize confusion, let's simply mark the
          hunk as modified.

        Returns:
            tuple: (first, last, [inserted], [modified], [deleted])
        """
        # first and last changed line in the view
        first, last = 0, 0
        # lists with inserted, modified and deleted lines
        inserted, modified, deleted = [], [], []
        hunk_re = r'^@@ \-(\d+), ?(\d*) \+(\d+),?(\d*) @@'
        for hunk in re.finditer(hunk_re, self._git_diff_cache, re.MULTILINE):
            # We don't need old_start in this function
            _, old_size, start, new_size = hunk.groups()
            start = int(start)
            # old_size and new_size can be null string
            # means only 1 line has been changed
            old_size = int(old_size or 1)
            new_size = int(new_size or 1)
            if first == 0:
                first = max(1, start)
            if not old_size:
                # this is a new added hunk
                last = start + new_size
                # [start, last)
                inserted += range(start, last)    
            elif not new_size:
                # the original hunk has been deleted
                # only save the starting line number
                last = start + 1
                deleted.append(last)
            else:
                last = start + new_size
                modified += range(start, last)
        return (first, last, inserted, modified, deleted)        

    def extract_diff_hunk(self, row):
        """
        Use cached diff result to extract the changes of the given row 

        Arguments:
            row (int): The row to find the diff-hunk for

        Returns:
            dictionary:  
                        {
                            # a string array contains the deleted lines
                            'deleted_lines': [],
                            
                            # a string array contains the added lines
                            'added_lines' : [],
                            
                            # the start position of this hunk in original file
                            # -1 if failed to find the hunk
                            'old_start_pos': int,

                            # the number of lines of this hunk in original file
                            # -1 if failed to find the hunk
                            'old_size' : int
                            
                            # the start position of this hunk in current file
                            # -1 if failed to find the hunk
                            'start_pos' : int,

                            # the number of lines of this hunk in current file
                            # -1 if failed to find the hunk
                            'size' : int,

                            # starting position of first hunk
                            # -1 if failed to find the hunk
                            'first_hunk_pos' : int, 
                            
                            # starting position of next hunk
                            # -1 if failed to find the hunk 
                            'next_hunk_pos' : int,
                            
                            # starting position of previous hunk
                            # -1 if failed to find the hunk
                            'prev_hunk_pos' : int,
                         
                        }

        """

        """
        Explanation:
        In this function we are looking for a hunk of lines that contains 
        given row(int). And then extract its deleted lines, new added lines...
        We mainly care about the deleted lines here. 

        In git diff, a diff hunk is displayed like this:

        @@ -24,4 +24 @@ Manage a Git repository
        -import os
        -import re
        -import gitjob
        -import tempfile
        +# add a new line

        "@@ -24,4 +24 @@ Manage a Git repository" 
        contains the information of the starting position of this hunk. 
        By iterating through all this kind of lines, we can locate the target hunk.

        The lines begin with '-' have been deleted from the current file. 
        The lines begin with '+' are the new added lines in current file.
        Then we extract the deleted lines and the added lines respectively. 
        """
        hunk_re = r'^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
        hunks = re.finditer(hunk_re, self._git_diff_cache, re.MULTILINE)
        # wrapping the hunk list to get surrounding hunks?
        wrap = True
        # extract the starting position of surrounding hunks
        first_hunk_pos = None
        prev_hunk_pos  = None 
        next_hunk_pos  = None
        
        for hunk in hunks:
            old_start, old_size, start, size = hunk.groups()
            old_start = int(old_start)
            old_size  = int(old_size or 1)
            start     = int(start)
            size      = int(size or 1)
            if first_hunk_pos is None:
                first_hunk_pos = start
            # special handling to also match the line below deleted content
            if size == 0 and row == start + 1:
                pass
            # continue if the hunk is before the line
            elif start + size < row:
                prev_hunk_pos = start
                continue
            # break if the hunk is after the line
            elif row < start:
                break
            

            # now we have found the hunk that contains the given row
            try:
                next_hunk = next(hunks)
                hunk_end = next_hunk.start()
                next_hunk_pos = int(next_hunk.group(3))
            except:
                hunk_end = len(self._git_diff_cache)

            if not wrap:
                if prev_hunk_pos  is None:
                    prev_hunk_pos  = start
                if next_hunk_pos is None:
                    next_hunk_pos = start

            # if prev change is None set it to the wrap around the
            # document: prev -> last hunk, next -> first hunk
            if prev_hunk_pos is None:
                try:
                    remaining_hunks = list(hunks)
                    if remaining_hunks:
                        last_hunk = remaining_hunks[-1]
                        prev_hunk_pos = int(last_hunk.group(3))
                    elif next_hunk_pos is not None:
                        prev_hunk_pos = next_hunk_pos
                    else:
                        prev_hunk_pos = start
                except:
                    prev_hunk_pos = start
            if  next_hunk_pos is None:
                next_hunk_pos = first_hunk_pos

            # extract the content of the hunk
            hunk_content = self._git_diff_cache[hunk.start():hunk_end]
            # skip first line: '@@ -[OLD_START],[OLD_SIZE] +[START],[SIZE] @@' 
            hunk_lines = hunk_content.splitlines()[1:]
            # store all deleted lines (starting with -)
            deleted_lines = [
                line[1:] for line in hunk_lines if line.startswith("-")
            ]
            # store all added lines (starting with +)
            added_lines = [
                line[1:] for line in hunk_lines if line.startswith("+")
            ]
            

            res = {
                'deleted_lines'  : deleted_lines,
                'added_lines'    : added_lines,
                'old_start_pos'  : old_start,
                'old_size'       : old_size, 
                'start_pos'      : start,
                'size'           : size,
                'first_hunk_pos' : first_hunk_pos,
                'next_hunk_pos'  : next_hunk_pos,
                'prev_hunk_pos'  : prev_hunk_pos
            }

            return res

        res = {
            'deleted_lines'  : [],
            'added_lines'    : [],
            'old_start_pos'  : -1,
            'old_size'       : -1, 
            'start_pos'      : -1,
            'size'           : -1,
            'first_hunk_pos' : -1,
            'next_hunk_pos'  : -1,
            'prev_hunk_pos'  : -1
        }    
    
        return res
    

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
        May raise a GitError exception
        """
        args = ['checkout', '-q', branch]
        self._git.run_blocking(args)

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
        args = ['remote', 'show']
        return self._git.run_blocking(args)

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
        
        args_name = ['config', 'branch.' + branch + '.remote']
        remote_name = self._git.run_blocking(args_name)

        args_merge = ['config', 'branch.' + branch + '.merge']
        remote_merge = self._git.run_blocking(args_merge)

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
