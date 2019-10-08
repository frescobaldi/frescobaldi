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
    Github
)

class Entity(object):
    """Common base class for repositories and organizations."""

    entity_base = None

    def __init__(self, path):

        self._path = path
        self._org = ''
        # This may forward various exceptions
        # (TODO: do we have to handle them here, or should this be done
        #  by the caller (i.e. in the GUI?)
        self._info = Github.get_json(self.base_url())

    def base_url(self):
        """Returns the Github API base URL for a repository."""
        return "https://api.github.com/" + self.entity_base + self.path()

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

    def name(self):
        """Return the organization's display name (if given),
        or its path name."""
        return self.info('name')

    def organization(self):
        """Return the organization path component.

        For an organization it is the URL name,
        for a repository it is the <org> component of the path.
        """
        return self._org

    def path(self):
        """Return the full path to the entity.

        In case of an organization it is simply the <org>,
        in case of a repository is is <org>/<repo>."""
        return self._path

    def url(self, path):
        """Return an arbitrary URL within the entity.

        If there is no path, then no slash will be appended to the URL.
        """
        base_url = self.base_url()
        if path:
            base_url = "{}/{}".format(base_url, path)
        return base_url
