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
import importlib

class VCSError(Exception):
    pass

# dict holding references to repo modules
# initially strings with module names,
# after first call to is_available the values
# point to the modules themselves.
_vcs_modules = {
    'git': "vcs.gitrepo"
}

def is_available(tool):
    """Returns True if the requested VCS software is available on the system.

    Supported vcs are:
    - 'git'
    - so far this is the only one

    Any NNNrepo.py module has to implement a function vcs_available()
    """
    if not tool in _vcs_modules.keys():
        raise VCSError('Invalid arguement for VCS software: {}\nSupported:\n- {}'.format(
            tool,
            "\n- ".join(_vcs_modules.keys())
        ))
    mod = _vcs_modules[tool]
    if type(mod) == str:
        mod = _vcs_modules[tool] = importlib.import_module(mod)
    return mod.Repo.vcs_available()


def app_is_git_controlled():
    """Return True if Frescobaldi is running from Git.

    This is done by checking for the presence of the .git/ directory.
    The function is very cheap, the directory test is only performed on the
    first call.

    """
    global _app_is_git_controlled
    try:
        return _app_is_git_controlled
    except NameError:
        _app_is_git_controlled = True
        if os.path.isdir(os.path.join(sys.path[0], '..', '.git')):
            if is_available('git'):
                from . import apprepo
                global app_repo
                app_repo = apprepo.Repo()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(None,
                                    _("Git not found"),
                                    _("Frescobaldi is run from within a Git "
                                      "repository, but Git does not appear "
                                      "to be working. Git support will be "
                                      "disabled. If you have Git installed, "
                                      "you can specify its location in the "
                                      "Preferences dialog."))
                _app_is_git_controlled = False
        else:
            _app_is_git_controlled = False
        return _app_is_git_controlled

# conditionally create app_repo object
app_is_git_controlled()

if app_is_git_controlled():
    # debugging tests, to be removed finally
    #from . import test
    pass

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

