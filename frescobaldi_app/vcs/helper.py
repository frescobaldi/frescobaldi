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

from PyQt5.QtCore import QObject

class VCSHelper(QObject):
    @classmethod
    def _is_vcs_path(cls, path):
        return path and os.path.exists(os.path.join(path, cls.meta_data_directory()))

    @classmethod
    def _extract_path(cls, ori_path):
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

            # files within meta_data_directory are not part of a work tree
            while path and name and name != cls.meta_data_directory():
                if cls._is_vcs_path(path):
                    return (path, os.path.relpath(
                        ori_path, path).replace('\\', '/'))
                path, name = os.path.split(path)

        return (None, None)


class GitHelper(VCSHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.git'

    @classmethod
    def extract_git_path(cls, path):
        return cls._extract_path(path)

class HgHelper(VCSHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.hg'

    @classmethod
    def extract_hg_path(cls, path):
        return cls._extract_path(path)

class SvnHelper(VCSHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.svn'

    @classmethod
    def extract_svn_path(cls, path):
        return cls._extract_path(path)

