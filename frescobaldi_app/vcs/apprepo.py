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
Repository of Frescobaldi application.
"""


import sys
import os

from . import gitrepo

class Repo(gitrepo.Repo):
    """
    Subclass to be used for the Frescobaldi Git repository.
    Offers methods exclusively useful for this specific repo.
    """
    def __init__(self):
        super(Repo, self).__init__((os.path.normpath(
                                        os.path.join(sys.path[0], '..'))))
        self._activeBranch = self.current_branch()

    def active_branch(self):
        """
        Returns the name of the branch that was current_branch
        when the application has started.
        current_branch() may of course change during the
        runtime of the application
        """
        return self._activeBranch
