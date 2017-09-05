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

from . import helper

class VCSError(Exception):
    pass

# dict holding references to helper classes
_vcs_helpers = {
    'git': helper.GitHelper,
#   'svn': helper.SvnHelper,
#   'hg' : helper.HgHelper
}

def is_available(tool):
    """Returns True if the requested VCS software is available on the system.

    Supported vcs are:
    - 'git'
    - so far this is the only one
    """
    if not tool in _vcs_helpers.keys():
       raise VCSError(_('Invalid argument for VCS software: {}\nSupported:\n- {}').format(
            tool,
          "\n- ".join(_vcs_helpers.keys())
       ))
    return _vcs_helpers[tool].vcs_available()


def app_active_branch_window_title():
    """Return the active branch, suitable as window title.

    If the app is not git-controlled, the empty string is returned.

    """
    if app_is_git_controlled():
        git_branch = app_repo.active_branch()
        return '({branch} [{remote}])'.format(
                branch=git_branch,
                remote=app_repo.tracked_remote_label(git_branch))
    return ''


def app_is_git_controlled():
    """Return True if Frescobaldi is running from Git."""
    global _app_is_git_controlled
    return _app_is_git_controlled

# Determine if Frescobaldi is run from Git by checking for
# both the presence of a .git directory and the availability of Git on the system.
_app_is_git_controlled = False
root_path, _ = helper.GitHelper.extract_vcs_path(sys.path[0])
if root_path is not None:
    if helper.GitHelper.vcs_available():
        from . import apprepo
        app_repo = apprepo.Repo()
        _app_is_git_controlled = True
    else:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(None,
                            "Git not found",
                            "Frescobaldi is run from within a Git "
                              "repository, but Git does not appear "
                              "to be working. Git support will be "
                              "disabled. If you have Git installed, "
                              "you can specify its location in the "
                              "Preferences dialog.")
