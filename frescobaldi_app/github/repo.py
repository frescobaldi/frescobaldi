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


import download

from . import (
    Github,
    GithubException,
    entity,
    node,
    tree
)

class Asset(entity.Item):
    """Represents a downloadable asset from a release."""

    def raw_url(self):
        return self._info['browser_download_url']


class Assets(entity.ItemCollection):
    """Represents the list of assets for a release."""

    _item_class = Asset


class Release(entity.Item):
    """Represents a release."""

    def __init__(self, info):
        super(Release, self).__init__(info)
        self._info['assets'] = {}

    def assets(self):
        """Return the collection of assets for this release."""
        if not self._info['assets']:
            self._info['assets'] = Assets(
                Github.get_json(self._info['assets_url'])
            )
        return self._info['assets']

    def source_url(self, format='zip'):
        """Return the download link for the source archive,
        either as zip or as tar.gz
        """
        k = 'zipball_url' if format == 'zip' else 'tarball_url'
        return self.info(k)

    def tag_name(self):
        """The Git tag from which this release is made."""
        return self.info('tag_name')


class Releases(entity.ItemCollection):
    """Represents the releases of a repository."""

    _name_key = 'tag_name'
    _item_class = Release

    def __iter__(self):
        """Iterate from newest to oldest."""
        self._iter_items = [n for n in self._items]
        self._iter_items.reverse()
        return self


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
        self._releases = {}

    def download_file(self, path, target, overwrite=False):
        """Download a file and save to disk.

        Verifies that the path is a file within the repository.
        Setting overwrite to True will allow writing over existing files.
        """
        # May raise a GithubException
        url = self.raw_file_url(path)
        # May raise download.FileExistsException or other OS relate errors
        download.download(url, target, overwrite=overwrite)

    def fetch(self, path):
        """Download a file and return its content.

        Verifies that the path is a file within the repository.
        """
        # May raise a GithubException
        url = self.raw_file_url(path)
        return download.fetch_content(self.raw_url(path))

    def name(self):
        """The name of a repository is its `repo` property."""
        return self.repo()

    def _paths(self, path=None, org=None, repo=None):
        """Process and return path, org and repo for a repository.

        Expects either path or org *and* repo to be provided.
        """
        if not (path or (org and repo)):
            # Don't translate that as it can only point to programming errors.
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

    def raw_file_url(self, path):
        """Returns the absolute download URL for an existing file.

        Verifies that path exists and points to a file.
        """
        node = self.tree().find_node(path)
        if not node or node.is_tree():
            raise GithubException(_(
                "Path '{path}'\n"
                "does not point to an existing file\n"
                "in Github repository {repo}"
            ).format(
                path=path,
                repo=self.path()
            ))
        return self.raw_url(path)

    def raw_url(self, path):
        """Return the absolute download URL for a resource.
        `path` can not be empty in this case.
        """
        return "https://raw.githubusercontent.com/{repopath}/{sha}/{path}".format(
            repopath=self.path(),
            sha=self.sha(),
            path=path
        )

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

    def releases(self):
        """Return a collection of releases."""
        if not self._releases:
            self._releases = Releases(Github.get_json(self.url('releases')))
        return self._releases

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
