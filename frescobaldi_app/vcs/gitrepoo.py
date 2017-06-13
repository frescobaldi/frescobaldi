import os
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

    def __init__(self):
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
        self._temp_Index_file = None
        self._temp_working_file = None  
    
    def __del__(self):
        """Caller is responsible for clean up the temp files"""
        if self._temp_committed_file:
            os.unlink(self._temp_committed_file)
        if self._temp_Index_file:
            os.unlink(self._temp_Index_file)
        if self._temp_working_file:
            os.unlink(self._temp_working_file)

    def set_working_directory(self, path):
        """
        Set the _root_path and _relative_path
        Return True if giving path is git initialized.  
        """
        self._root_path, self._relative_path = self._get_work_path(path)
        return self._root_path != None
       

    def _is_git_path(self, path):
        """
        Return True if 'path' is a valid git working tree.
        """
        return path and os.path.exists(os.path.join(path, '.git'))
    

    def _get_work_path(self, ori_path):
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
        if ori_path and os.path.exists(ori_path):
            if os.path.isdir(ori_path):
                _, name = os.path.split(ori_path)
                path = ori_path
            else:
                path, name = os.path.split(ori_path)    
            
            # files within '.git' path are not part of a work tree
            while path and name and name != '.git':
                if self._is_git_path(path):
                    return (path, os.path.relpath(
                        ori_path, path).replace('\\', '/'))
                path, name = os.path.split(path)
        
        return (None, None)
    
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
    
    def _update_temp_Index_file(self):
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
            if not self._temp_Index_file:
                self._temp_Index_file = self._create_tmp_file()
            # Write content to temp file
            with open(self._temp_Index_file, 'wb') as file:
                file.write(content)
    
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