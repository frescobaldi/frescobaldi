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

import os
import re

from PyQt5.QtCore import QObject, QProcess

class VCSHelper(QObject):
    @classmethod
    def _is_vcs_path(cls, path):
        return path and os.path.exists(os.path.join(path, cls.meta_data_directory()))

    @classmethod
    def extract_vcs_path(cls, ori_path):
        # ensure there is no trailing slash
        sep = os.path.altsep if os.path.altsep else ''
        sep += os.path.sep
        ori_path = ori_path.rstrip(sep)
        if ori_path and cls.check_path_permissions(ori_path):
            if os.path.isdir(ori_path):
                _, name = os.path.split(ori_path)
                path = ori_path
            else:
                path, name = os.path.split(ori_path)

            # files within meta_data_directory are not part of a work tree
            while path and name and name != cls.meta_data_directory():
                if cls._is_vcs_path(path):
                    if cls.check_path_permissions(path):
                        return (path, os.path.relpath(
                            ori_path, path).replace('\\', '/'))
                    else:
                        break
                path, name = os.path.split(path)

        return (None, None)

    @classmethod
    def check_path_permissions(cls, path):
        """
        Return True if Frescobaldi can read and write in 'path'
        """
        return os.access(path, os.F_OK | os.R_OK | os.W_OK)

class GitHelper(VCSHelper):

    _version = None
    _checked = False

    error_message = {
        QProcess.FailedToStart : 'Git failed to start',
        QProcess.Crashed : 'Git crashed',
        QProcess.Timedout : 'Time running out',
        QProcess.ReadError : 'ReadError',
        QProcess.WriteError : 'WriteError',
        QProcess.UnknownError : 'UnknownError'
    }

    @classmethod
    def vcs_available(cls):

        def result_parser(gitprocess, exitcode):
            output = gitprocess.stdout()
            # Parse version string like (git version 2.12.2.windows.1)
            match = re.match(r'git version (\d+)\.(\d+)\.(\d+)', output[0])
            if match:
                # PEP-440 conform git version (major, minor, patch)
                cls._version = tuple(int(g) for g in match.groups())
            else:
                cls._version = None

        def error_catcher(error_code):
            cls._version = None

        if not cls._checked:
            from . import gitjob
            args = ['--version']
            git = gitjob.Git(None)
            git.preset_args = args
            git.errorOccurred.connect(error_catcher)
            git.finished.connect(result_parser)
            git.run_blocking()
            cls._checked = True

        return cls.vcs_version() is not None

    @classmethod
    def vcs_version(cls):
        return cls._version

    @classmethod
    def meta_data_directory(cls):
        return '.git'

class HgHelper(VCSHelper):

    _version = None
    _checked = False

    @classmethod
    def vcs_available(cls):
        # TODO: implement this function
        return cls.vcs_version() is not None

    @classmethod
    def vcs_version(cls):
        return cls._version

    @classmethod
    def meta_data_directory(cls):
        return '.hg'


class SvnHelper(VCSHelper):

    _version = None
    _checked = False

    @classmethod
    def vcs_available(cls):
        # TODO: implement this function
        return cls.vcs_version() is not None

    @classmethod
    def vcs_version(cls):
        return cls._version

    @classmethod
    def meta_data_directory(cls):
        return '.svn'


