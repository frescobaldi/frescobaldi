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
VCS interface (application and documents)
"""

from __future__ import unicode_literals

import sys
import os

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
        _app_is_git_controlled = os.path.isdir(os.path.join(sys.path[0], '..', '.git'))
    return _app_is_git_controlled

if app_is_git_controlled():
    from . import apprepo
    app_repo = apprepo.AppRepo()
    
    # debugging tests, to be removed
    from . import test

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

