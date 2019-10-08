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
Working with Github repositories
"""


from . import (
    Github,
    GithubException,
    entity,
    node,
    tree
)


class Repo(entity.Entity):
    """Represents a Github repository at a given branch or commit."""

    # NOTE: self._info includes rich repository metadata that can be
    # made available as properties when needed. So far only very few
    # have been implemented (e.g. description())

    entity_base = 'repos/'

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
        path, org, repo = self._paths(path, org, repo)
        super(Repo, self).__init__(path)
        self._org, self._repo = org, repo
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
            self.tree_url(sha=(sha + recursive))
        )
        self._tree = tree.Tree(json_data)

    def _paths(self, path=None, org=None, repo=None):
        """Process and return path, org and repo for a repository.

        Expects either path or org *and* repo to be provided.
        """
        if not (path or (org and repo)):
            raise GithubException(
                "Invalid repository target:\n"
                "path: {path}"
                "org: {org}"
                "repo: {repo}".format(path=path, org=org, repo=repo)
            )
        if path:
            return (path, *path.split('/'))
        else:
            return ("{org}/{repo}".format(org=org, repo=repo), org, repo)

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
        data = Github.get_json(self.tree_url(sha=sha, path=path))
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

    def tree_url(self, path=None, sha=None):
        """Returns the URL for an object in the repository tree.

        If `sha` is not provided the base SHA from which the repository
        has been loaded.
        If `path` is given (as a forward-slash-separated string) the URL
        of the corresponding element in the tree is retrieved,
        the root of the tree otherwise.
        """
        base = "git/trees/" + (sha or self.sha())
        path = base + "/" + path if path else base
        return self.url(path)
