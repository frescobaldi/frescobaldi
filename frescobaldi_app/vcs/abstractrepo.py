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
from abc import ABCMeta, abstractmethod

class AbstractVCSRepo(object):
    """
    Interface for classes managing VCS repositories.
    Currently we only support Git, but this level of
    abstraction is intended to offer an interface to
    add other VCS comparably easily.
    """
    __metaclass__ = ABCMeta

    @classmethod
    def vcs_available(cls):
        """
        Returns True if the respective VCS is installed
        """
        raise NotImplementedError()

    @abstractmethod
    def branches(self, local=True):
        """
        Returns a string list of branch names.
        If local is False also return 'remote' branches.
        """
        pass

    @abstractmethod
    def checkout(self, branch):
        pass

    @abstractmethod
    def current_branch(self):
        """
        Returns the name of the current branch.
        """
        pass

    @abstractmethod
    def has_branch(self, branch):
        """
        Returns True if the given branch exists.
        Checks by actually running git branch.
        """
        pass

    @abstractmethod
    def has_remote(self, remote):
        """Returns True if the given remote name is registered."""
        pass

    @abstractmethod
    def has_remote_branch(self, branch):
        """
        Return True if the given branch
        is tracking a remote branch.
        """
        pass

    @abstractmethod
    def remotes(self):
        """Return a string list with registered remote names"""
        pass

    @abstractmethod
    def tracked_remote(self, branch):
        """
        Return a tuple with the remote and branch tracked by
        the given branch.
        In most cases both values will be identical, but a branch
        can also track a differently named remote branch.
        Return ('local', 'local') if it doesn't track any branch.
        """
        pass

    @abstractmethod
    def tracked_remote_label(self, branch):
        """
        Return a string to be used for remote branch info.
        Either 'local', the remote name or remote/branch.
        """
        pass
