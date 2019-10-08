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
Working with Github organizations and repositories
"""

from . import (
    Github,
    node,
    tree
)


class Repo(object):
    """Represents a Github repository at a given branch or commit."""

    # NOTE: self._info includes rich repository metadata that can be
    # made available as properties when needed. So far only very few
    # have been implemented (e.g. description())

    def __init__(
        self,
        path=None,
        org=None,
        repo=None,
        sha='master',
        recursive=True
    ):
        """Create a repository object from Github.

        This requires *either* a full "<organization>/<repository>" path
        *or* both the organization and the repository keyword arguments.
        `sha` may be either a branch or an arbitrary commit SHA.
        `recursive` determines whether the whole tree structure will
        be downloaded immediately or only upon request
        (NOTE: This has not been implemented yet, so far the tree will
        always be initialized immediately.)

        """
        self._path, self._org, self._repo = Github.repo_paths(path, org, repo)
        # This may forward various exceptions
        # (TODO: do we have to handle them here, or should this be done
        #  by the caller (i.e. in the GUI?)
        self._info = Github.get_json(Github.repo_url(self, ''))
        self._sha = sha
        # TODO: Not implemented yet
        # recursive = '?recursive=1' if recursive else ''
        recursive = '?recursive=1'
        # Initialize the git/tree object and download either the JSON
        # representation of the full repository or the top-level directory
        # (depending on the `recursive` argument)
        # Retrieve information about the full repository tree from the current
        # SHA/branch.
        # NOTE:
        # It may be possible that for very large repositories not all nodes
        # are returned from Github. In that case statistical functions may not
        # work properly, and nodes not initially retrieved will be updated
        # upon request too. This hasn't been dealt with yet!
        # NOTE: May forward various exceptions
        json_data = Github.get_json(
            Github.repo_tree_url(self, sha + recursive)
        )
        self._tree = tree.Tree(json_data)

    def description(self):
        """Return the repository description."""
        return self.info('description')

    def info(self, item=None):
        """
        Return repository information, either the whole dataset (if item=None)
        or a single value.
        """
        if item:
            return self._info[item]
        else:
            return self._info

    def organization(self):
        """Return the organization (string) this repository belongs to."""
        return self._org

    def path(self):
        """Return the full <org>/<repo> path to the repository."""
        return self._path

###
#
# TODO: This is preliminary and must be fleshed out
# (and probably wouldn't work anymore without modification).
# The plan is to read the JSON data from a repository's directory
# (in cases where not the whole data for a repository has to be retrieved
# or where the response had been truncated.)
# This will implicitly be called when non-existent nodes are requested
# and self._completed is not True

    def read_dir(
        self,
        path,
        sha,
        recursive=False
    ):
        result = {}
        data = Github.get_json(Github.repo_tree_url(self, sha=sha, path=path))
        for element in data['tree']:
            new_node = node.Node(path, element)
            if new_node.is_tree():
                new_node.set_children(self.read_dir(
                    path + [new_node.name()],
                    new_node.sha(),
                    True
                ))
            result[element['path']] = new_node

#
###

    def repository(self):
        """Return the repository name."""
        return self._repo

    def sha(self):
        """Return the SHA/branch this Repo object is loaded from."""
        return self._sha

    def tree(self):
        """Return the directory tree instance (Tree object)."""
        return self._tree
