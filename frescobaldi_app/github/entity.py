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
Working with Github organizations, repositories and other items
"""

import collections

from . import (
    Github
)


class Item(object):
    """Base class for all Github items.

    An item is an object that manages information about a single object
    retrieved from a Github API endpoint. It is created from an 'info'
    dictionary which has already been retrieved through Github.get_json(url).

    Arbitrary properties can be accessed through info(), while *some* of them
    are made available as regular properties.

    """

    # info field containing the "name" of the item,
    # may be overwritten in subclasses
    _name_key = 'name'

    def __init__(self, info):
        """Initialize the object with its info data. Must be a dictionary."""
        self._info = info

    def info(self, item=None):
        """Returns either the info dictionary or one element."""
        if item:
            return self._info.get(item, None)
        else:
            return self._info

    def name(self):
        """
        Returns the "display name" of the item, determined
        by the field specified in the _name_key class variable.
        """
        return self.info(self._name_key)

    def raw_url(self):
        """
        Returns the URL of the downloadable item
        (if implemented in a subclass).
        """
        pass


class ItemCollection(object):
    """Represents a collection of repository items.

    The collection is iterable and will consist of a number of items
    of the same class. The items are stored in order of insertion but
    can also retrieved by name. The "name" is the value of an item's
    field specified by the _name_key class variable.

    In simple cases subclassing does enough by specifying an _item_class class
    variable. In more complex situations it may be necessary to override
    _create_item() (which will implicitly be called by add_item()).
    """

    _name_key = 'name'
    _item_class = None

    def __init__(self, items):
        """Initialize the object with items.

        `items` is a list of item definition dictionaries.
        """
        self._items = collections.OrderedDict()
        for item in items:
            self.add_item(item)

    def __iter__(self):
        self._iter_items = [n for n in self._items]
        return self

    def __next__(self):
        if self._iter_items:
            name = self._iter_items.pop()
            return self._items[name]
        else:
            raise StopIteration

    def add_item(self, item):
        """Add an item to the collection.

        Called by the initializer and calling _create_item()
        to be overridden for more complex cases.
        """
        self._items[item[self._name_key]] = self._create_item(item)

    def by_name(self, name):
        """Return an item by its name."""
        return self._items.get(name, None)

    def _create_item(self, item):
        """Create an item.

        If the _item_class class variable is set cretae an object from that
        class. Should be overridden where this is not sufficient.
        """
        if self._item_class:
            return self._item_class(item)


class Entity(Item):
    """Common base class for repositories and organizations.

    An Item with more specific properties and functionality.
    """

    # initial element for the entity's base url.
    # Must be specified in subclasses
    entity_base = None

    def __init__(self, path):
        """Initialize the entity.

        Other than simple Items an Entity will load its info dictionary
        from a URL that it determines.
        """
        self._path = path
        self._org = ''
        super(Entity, self).__init__(Github.get_json(self.base_url()))

    def base_url(self):
        """Returns the Github API base URL for a repository."""
        return "https://api.github.com/" + self.entity_base + self.path()

    def description(self):
        """Return the entity#s description."""
        return self.info('description')

    def name(self):
        """Override the naming from Item."""
        return self.path()

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
