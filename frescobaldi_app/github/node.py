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
Handling Nodes in a Github repository.
"""


class Node(object):
    """Represents a node in a Github repository tree."""

    def __init__(self, data):
        """
        Create a Node from data passed in from Github,
        representing either a blob (file object) or a tree (directory).
        `data` is a dictionary provided by the Github API.
        The caller will add the new Node object as a child to another node
        or the repository tree's root node.
        """
        self._parent_node = None
        self._path = data['path']
        last_sep = self._path.rfind('/')
        if last_sep == -1:
            self._parent = ''
            self._name = self._path
        else:
            self._parent = self._path[:last_sep]
            self._name = self._path[last_sep + 1:]
        self._mode = data['mode']
        self._type = data['type']
        self._sha = data['sha']
        self._url = data['url']
        if self._type == 'tree':
            self._children = {}
        else:
            self._size = data['size']

    def add_child(self, node):
        """Add a child node (if self is a tree node)."""
        if not self.is_tree():
            raise AttributeError('This node is a blob, not a tree')
        self._children[node.name()] = node
        node.set_parent(self)

    def children(self):
        """Return a list of the node's children, sorted by name."""
        if not self.is_tree():
            raise AttributeError('This node is a blob, not a tree')
        for k in sorted(self._children.keys(), key=str.lower):
            yield self._children[k]

    def child_by_name(self, name):
        """Return a child node by its name, or None if noone exists."""
        if not self.is_tree:
            raise AttributeError('This node is a blob, not a tree')
        return self._children.get(name, None)

    def is_tree(self):
        """Returns True if the node represents a tree (directory),
        False in case of a blob (file)."""
        return self._type == 'tree'

    def mode(self):
        """Returns the node's file mode."""
        return self._mode

    def name(self):
        """Returns the node's (base)name.
        This is the file/dir name within the directory"""
        return self._name

    def parent(self):
        """Return the path (string) to the parent element."""
        return self._parent

    def parent_node(self):
        """Return the parent (node), or None if self is the root node."""
        return self._parent_node

    def set_parent(self, parent):
        """Store reference to parent node."""
        self._parent_node = parent

    def path(self):
        """Full name of the object in the repository.
        Note this always uses forward slashes as separators,
        and paths never start with a slash."""
        return self._path

###
#
# NOTE: This is probably obsolete, currently used in Repo.read_dir()

    def set_children(self, children):
        self._children = children

#
###

    def sha(self):
        """Return the node's SHA.

        This refers to the blob/tree at the current branch or commit
        from which the Repo object has been created.
        """
        return self._sha

    def type(self):
        """Returns 'tree' (directory) or 'blob' (file)."""
        return self._type

    def url(self):
        """Returns the (API) URL of the node.

        For trees this URL will return a JSON object

        TODO: What does this refer in blobs?
        I think I was wrong, this actually *also* references a JSON object, not the actual file (which can then be retrieved from the JSON)

        """
        return self._url
