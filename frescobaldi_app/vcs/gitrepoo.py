import os

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
