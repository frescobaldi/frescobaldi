import os
import gitjob

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
    def branches(self):
        pass
    def current_branch(self):
        pass
    def has_branch(self):
        pass
    def has_remote(self):
        pass 

    def __init__(self):
        # update signal emits signal when git content updates
        self._update_signal = pyqtSignal(bool)
        # git command instance
        self._git = gitjob.Git()
        # root path of current working directory
        self._root_path = None
        # current file/directory's relative path
        self._relative_path = None

    def set_working_directory(self, path):
        """
        Set the _root_path and _relative_path
        Return True if giving path is git initialized.  
        """
        self._root_path, self._relative_path = self._get_work_path(path)
        return self._root_path == None
       

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