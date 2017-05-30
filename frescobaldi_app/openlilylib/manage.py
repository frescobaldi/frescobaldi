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
openLilyLib package management
"""

import os

import vcs

def checkRoot(root):
    root_exists = os.path.isdir(root)
    is_ready = root_exists and not os.listdir(root)
    if is_ready:
        return root
    if root_exists:
        # TODO: ask if change/continue/abort
        return ''
    # TODO: Ask if create directory
    return ''

def askGit():
    """Ask the user whether to use Git for the installation/update or not."""
    #TODO: Create dialog
    return True

def installOll(root):
    """Downloads and installs the basic OLL infrastructure in the given root directory.
    Returns the (modified) root directory or False if failed or aborted.
    Is careful not to overwrite existing content.
    """
    newRoot = checkRoot(root)
    if not newRoot:
        return False
    gitAvailable = vcs.is_available('git')
    useGit = gitAvailable and askGit()

    #TODO: Implement:
    # if git: HTTPS/SSH
    # Download/clone oll-core
    # when that is done: result = True

    return False

def installPackage(package):
    """Downloads and installs a given package.
    Returns the package name or False."""
    return False

def installPackages(packages = None):
    """Install one or more openLilyLib packages from Github.
    Returns a list of installed package names"""
    result = []
    if packages is None:
        #TODO: Create dialog
        packages = []
    for p in packages:
        result.append(installPackage(p))
    return result