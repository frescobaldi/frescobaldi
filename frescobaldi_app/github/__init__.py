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
Working with Github repositories and organizations
"""

import json
import urllib.error
import urllib.request

from download import (
    fetch_content,
    ServerException,
    NotFoundException
)

class GithubException(Exception):
    pass


class JSONException(Exception):
    """Exception from JSON converion

    Has fields
    - message: original exception's message
    - url: Github URL from which the JSON was retrieved
    """
    def __init__(self, e, url):
        # TODO: Make message translatable after testing
        self.message = str(e)
        self.url = url
        error = (
            "Invalid JSON retrieved from Github\n"
            "Error: {e}\nURL: {url}".format(e=e, url=url)
        )
        super(JSONException, self).__init__(error)


class Github(object):
    """Static class providing Github-related functionality."""

    @classmethod
    def get_json(cls, url):
        """Loads a JSON object through Github API and returns a dictionary."""
        # May raise
        # download.ServerException or
        # download.NotFoundException
        raw_json = fetch_content(url)
        # May raise github.JSONException
        return Github.load_json(raw_json, url)

    @classmethod
    def load_json(cls, raw_json, url):
        """Create a dictionary from a JSON string.

        Raises an exception including the original exception and the url
        if anything goes wrong.
        """
        try:
            result = json.loads(raw_json)
        except Exception as e:
            raise JSONException(e, url)
        return result

    @classmethod
    def repo_base_url(cls, repo):
        """Returns the Github API base URL for a repository."""
        return "https://api.github.com/repos/" + repo.path()

    @classmethod
    def repo_paths(cls, path=None, org=None, repo=None):
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

    @classmethod
    def repo_tree_url(cls, repo, sha=None, path=None):
        """Returns the URL for an object in the repository tree.

        If `sha` is not provided the base SHA from which the repository
        has been loaded.
        If `path` is given (as a forward-slash-separated string) the URL
        of the corresponding element in the tree is retrieved,
        the root of the tree otherwise.
        """
        base = "git/trees/" + (sha or repo.sha())
        path = base + "/" + path if path else base
        return Github.repo_url(repo, path)

    @classmethod
    def repo_url(cls, repo, path):
        """Return an arbitrary URL within the repository.

        If there is no path, then no slash will be appended to the URL.
        """
        base_url = Github.repo_base_url(repo)
        if path:
            base_url = "{}/{}".format(base_url, path)
        return base_url
