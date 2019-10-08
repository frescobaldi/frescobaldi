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
Working with Github organizations
"""


from . import (
    Github,
    entity
)


class Organization(entity.Entity):
    """Represents a Github organization."""

    entity_base = 'orgs/'

    def __init__(self, org):
        """Create an organization object from Github."""
        super(Organization, self).__init__(org)
        self._org= org
        self._repo_names = []
        self._repositories = {}

    def repo_info(self, name):
        """Return the info dictionary for a given repository."""
        repos = self.repositories()
        return repos.get(name, None)

    def repositories(self):
        """Returns a dict of repository info dictionaries.

        Each dictionary corresponds to the info() of a Repo object.
        """
        if not self._repositories:
            repos_info = Github.get_json(self.url('repos'))
            for r in repos_info:
                name = r['name']
                self._repo_names.append(name)
                self._repositories[name] = r
        return self._repositories

    def repository_names(self, sort=True):
        """Return an (optionally sorted) list of repository names."""
        self.repositories()
        if sort:
            return sorted(self._repo_names)
        else:
            return self._repo_names
