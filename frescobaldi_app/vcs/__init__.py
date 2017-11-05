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

import sys
import os

from PyQt5.QtCore import QSettings

import app
from . import (
    gitrepo, 
    apprepo, 
    gitdoc, 
    gitjob
)

class VCSError(Exception):
    pass

class VCS(object):
    """
    Static class providing tool functions for use with VCS.
    """

    # global configuration for supported VCS types
    meta = {
        'git': {
            'manager_class': gitrepo.RepoManager,
            'repo_manager': None,
            'meta_directory': '.git',
            'document_class': gitdoc.Document,
            'job_class': gitjob.Job,
            'version': None
        },
        'hg': {
            'manager_class': None,
            'repo_manager': None,
            'meta_directory': '.hg',
            'document_class': None,
            'job_class': None,
            'version': False
        },
        'svn': {
            'manager_class': None,
            'repo_manager': None,
            'meta_directory': 'unsupported',
            'document_class': None,
            'job_class': None,
            'version': False
        }
    }
    
    # convenience methods for cleaner access to the meta information
    # no checks are performed for valid vcs_type arguments,
    # so if asked about an unsupported VCS string (not present in the
    # 'meta' dictionary) a KeyError will be thrown.
    @classmethod
    def repo_manager(cls, vcs_type):
        """
        Return the RepoManager instance responsible for maintaining
        all active repositories of the given type.
        """
        if not cls.is_available(vcs_type):
            return None
        if cls.meta[vcs_type]['repo_manager'] is None:
            cls.meta[vcs_type]['repo_manager'] = cls.meta[vcs_type]['manager_class']()
        return cls.meta[vcs_type]['repo_manager']
    
    @classmethod
    def meta_directory(cls, vcs_type):
        """
        Return the name of the meta directory whose presence indicates
        the root directory of a repository of the given type.
        """
        return cls.meta[vcs_type]['meta_directory']
    
    @classmethod
    def document_class(cls, vcs_type):
        """
        Return the class (not an object) of the VCS document responsible
        for documents in a repository of the given type.
        """
        return cls.meta[vcs_type]['document_class']
    
    @classmethod
    def job_class(cls, vcs_type):
        """
        Return the class (not an object) of the VCS Job subclass responsible
        for the given VCS type.
        """
        return cls.meta[vcs_type]['job_class']

    @classmethod
    def version(cls, vcs_type):
        """
        Return the installed version of the given VCS type
        or False if it's not available.
        """
        if cls.meta[vcs_type]['version'] is None:
            cls.meta[vcs_type]['version'] = cls.job_class(vcs_type).version() \
                if cls.job_class(vcs_type) is not None else False
        return cls.meta[vcs_type]['version']

    @classmethod
    def is_available(cls, vcs_type=None):
        """
        Return True if the given VCS is installed (and found)
        or False if not.
        If no VCS string is given return True if *any* of the supported
        VCSs is installed.
        """
        if vcs_type is None:
            for v in cls.meta:
                if cls.is_available(v):
                    return True
            return False
        else:
            return cls.version(vcs_type) != False

    @classmethod
    def use(cls, vcs_type=None):
        """
        Return True if the given VCS tool should be used for tracking documents.
        So far only Git support is implemented.
        Git support is shielded by the "experimental features" check.
        If no VCS type is given return True if *any* supported VCS is available.
        """
        if not (App.is_git_controlled() or
                QSettings().value("experimental-features", False, bool)):
            # Use of VCS is generally disabled
            return False
        
        # use of a VCS is determined by its availability
        return VCS.is_available(vcs_type)

    @classmethod
    def repo_root_type(cls, path):
        """
        Check if path points to the root of a VCS repository.
        Return the name of the VCS if found, otherwise False.
        """
        if not os.path.isdir(path):
            return False
        for vcs_name in VCS.meta:
            if os.path.exists(os.path.join(path, VCS.meta_directory(vcs_name))):
                return vcs_name
        return False

    @classmethod
    def vcs_path_info(cls, full_path):
        """
        Determine if path represents a file in the working tree of a supported
        VCS repository. This is agnostic of whether the file is tracked or not.
        Return a tuple of vcs_type, repository_root, relative_path.
        Otherwise return a 'None' 3-tuple.
        """

        # ensure there is no trailing slash
        sep = os.path.altsep if os.path.altsep else ''
        sep += os.path.sep
        path = full_path.rstrip(sep)

        # We are only interested in writable files,
        # write-protected files can't be versioned anyway
        if os.access(full_path, os.F_OK | os.W_OK):

            # We are working on files only and know that path represents a file
            # (and not a directory).
            path = os.path.split(path)[0]

            root_name = os.path.abspath(os.sep)
            while path != root_name:
                vcs_type = VCS.repo_root_type(path)
                if vcs_type:
                    return (vcs_type, path,          # TODO: is this replace necessary?
                            os.path.relpath(full_path, path).replace('\\', '/'))
                path = os.path.split(path)[0]

        return (None, None, None)

    @classmethod
    def instantiate_doc(cls, url, view):
        """
        Test if the given url represents a document in a repository.
        Return either an instance of the corresponding document class or (None, None).
        This is independent from the tracking state of the document.
        """
        vcs_type, root_path, relative_path = VCS.vcs_path_info(url.path())
        
        if not vcs_type:
            return (None, None)
        doc_class = VCS.document_class(vcs_type)
        instance = doc_class(root_path, relative_path, view)
        return (vcs_type, instance)

    @classmethod
    def invalidate(cls):
        """
        Respond to changes in settings and update the VCS subsystem accordingly.
        """
        # TODO: To be implemented
        # - maybe go through all supported systems and call invalidate() on
        #   the RepoManager instance
        # - it is important to update the editor/view (diff area, statusbar)
        # - maybe more ...
        pass

app.settingsChanged.connect(VCS.invalidate)

class App(object):
    """
    Static class representing Frescobaldi as run from the Git repository
    """
        
    # Determine if Frescobaldi is run from Git by checking for
    # both the presence of a .git directory and the availability of Git on the system.
    _is_git_controlled = None
    _active_branch_window_title = None
    repo = None

    @classmethod
    def is_git_controlled(cls):
        """
        Return True if Frescobaldi is running from Git.
        If the Frescobaldi executable is within a Git repository
        but Git is not found, display a warning and return False.
        """
        
        if cls._is_git_controlled is None:
            frescobaldi_root = os.path.normpath(os.path.join(sys.path[0], '..'))
            if VCS.repo_root_type(frescobaldi_root):
                if VCS.is_available('git'):
                    from . import apprepo
                    cls.repo = apprepo.Repo(frescobaldi_root)
                    cls._is_git_controlled = True
                else:
                    cls._is_git_controlled = False
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(None,
                                        "Git not found",
                                        "Frescobaldi is run from within a Git "
                                        "repository, but Git does not appear "
                                        "to be working. Git support will be "
                                        "disabled. If you have Git installed, "
                                        "you can specify its location in the "
                                        "Preferences dialog.")
            else:
                cls._is_git_controlled = False
        return cls._is_git_controlled

    @classmethod
    def active_branch_window_title(cls):
        """Return the active branch, suitable as window title.
        The branch is always the one that was checked out upon application start,
        so it can be cached.
        If the app is not git-controlled, an empty string is returned.
        """
        if cls._active_branch_window_title is None:
            if cls.is_git_controlled():
                git_branch = cls.repo.active_branch()
                cls._active_branch_window_title = '({branch} [{remote}])'.format(
                        branch=git_branch,
                        remote=cls.repo.tracked_remote_label(git_branch))
            else:
                cls._active_branch_window_title = ''
        return cls._active_branch_window_title
