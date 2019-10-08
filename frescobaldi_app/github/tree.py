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
Represents a tree in a Github repository
"""


from . import node


class Tree(object):
    """Represents the repository tree."""

    def __init__(self, json_data):
        """Initialize with an empty root node."""
        self._root = node.Node({
            'path': '',
            'mode': '040000',
            'type': 'tree',
            'sha': json_data['sha'],
            'url': json_data['url']
        })
        self._paths = {}
        self._truncated = json_data['truncated']
        for element in json_data['tree']:
            self.new_node(element)

    def add_node(self, node):
        """Hook a node into the tree."""
        path = node.path()
        parent = node.parent()
        name = node.name()
        self._paths[path] = node
        parent_node = self.find_node(parent)
        # TODO: Handle case when that's empty
        parent_node.add_child(node)

    def directory(self, path, dir=True, file=True):
        parent = self.find_node(path)
        if not parent:
            raise ValueError("Directory not found: " + path)
        elif not parent.is_tree():
            raise ValueError(path + " is not a directory")
        result = []
        for child in parent.children():
            is_tree = child.is_tree()
            if (
                dir and is_tree
                or file and not is_tree
            ):
                result.append(child)
        return result

    def _find_node(self, path, root):
        """Find a node through recursively visiting nodes.
        NOTE: This is probably obsolete because add_node()
        adds each node to the self._paths dictionary."""
        if not root:
            return None
        if type(path) == str:
            path = path.split('/')
        if path in [[], ['']]:
            return root
        elif len(path) == 1:
            return root.child_by_name(path[0])
        else:
            return self.find_node(path[1:], root.child_by_name(path[0]))

    def find_node(self, path, root=None):
        """Return a node matching the path, or None.

        `path` is a string relative to the given or the repository root.
        If `root` is given it is used to find the node, otherwise
        the repository root.

        """
        root = root or self._root
        if not path:
            return root
        r_path = root.path()
        if r_path:
            path = '{}/{}'.format(root.path(), path)
        return self._paths.get(path, None)

    def new_node(self, element):
        """Create and add a node.

        `element` is a dictionary with the JSON data retrieved from Github.
        """
        self.add_node(node.Node(element))

    def root(self):
        """Return the repository's root node."""
        return self._root
