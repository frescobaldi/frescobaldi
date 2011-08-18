# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

The Node class.

(c) 2008-2011 Wilbert Berendsen
License: GPL.

This module contains the Node class that can be used as a simple DOM (Document
Object Model) for building a tree structure.

A Node has children with list-like access methods and keeps also a weak
reference to its parent. A Node can have one parent; appending a Node to another
Node causes it to be removed from its parent node (if any).

You should inherit from Node to make meaningful tree node types.

"""

from __future__ import unicode_literals


import weakref


class Node(object):
    
    def __init__(self, parent=None):
        self._parent = None
        self._children = []
        if parent:
            parent.append(self)

    def parent(self):
        """
        The parent, or None if the node has no parent.
        """
        if self._parent is not None:
            return self._parent()

    def children(self):
        """
        Our children, may be an empty list.
        """
        return self._children

    def setParent(self, parent):
        """
        Takes away node from current parent and appends to other.
        """
        if parent is not self.parent():
            parent.append(self)
    
    def removeFromParent(self):
        """
        Removes self from parent.
        """
        parent = self.parent()
        if parent:
            parent.remove(self)

    def append(self, node):
        """
        Appends an object to the current node. It will be reparented, that
        means it will be removed from it's former parent (if it had one).
        """
        assert isinstance(node, Node)
        node.removeFromParent()
        self._children.append(node)
        node._parent = weakref.ref(self)
        
    def extend(self, iterable):
        """
        Calls append() for every Node from iterable.
        """
        for node in iterable:
            self.append(node)
        
    def index(self, node):
        """
        Return the index of the given object in our list of children.
        """
        return self._children.index(node)

    def insert(self, where, node):
        """
        Insert at index, or just before another node.
        """
        assert isinstance(node, Node)
        if isinstance(where, Node):
            where = self.index(where)
        node.removeFromParent()
        self._children.insert(where, node)
        node._parent = weakref.ref(self)
        
    def remove(self, node):
        """
        Removes the given child object.
        See also: removeFromParent()
        """
        self._children.remove(node)
        node._parent = None

    def replace(self, where, node):
        """
        Replace child at index or specified node with a replacement node.
        """
        assert isinstance(node, Node)
        if isinstance(where, Node):
            old = where
            where = self.index(where)
        else:
            old = self._children[where]
        node.removeFromParent()
        node._parent = weakref.ref(self)
        self._children[where] = node
        old._parent = None

    def __nonzero__(self):
        """ We are always true """
        return True
    
    def __len__(self):
        """ Return the number of children """
        return len(self._children)

    def __getitem__(self, k):
        """ also supports slices """
        return self._children[k]

    def __setitem__(self, k, obj):
        """ also supports slices """
        if isinstance(k, slice):
            if k.step:
                # extended slice, number of items must be same
                if len(obj) == len(self[k]):
                    for new, old in zip(obj, self[k]):
                        self.replace(old, new)
                else:
                    raise ValueError, \
                        "extended slice and replacement must have same length"
            else:
                del self[k]
                start = k.start or 0
                # save the obj iterator results because obj could change ...
                for d, new in enumerate(tuple(obj)):
                    self.insert(start + d, new)
        else:
            self.replace(k, obj)

    def __delitem__(self, k):
        """ also supports slices """
        if isinstance(k, slice):
            for i in self[k]:
                self.remove(i)
        else:
            self.remove(self[k])

    def __contains__(self, node):
        return node in self._children

    def clear(self):
        """ Remove all children """
        del self[:]

    def copy(self):
        """ Return a deep copy of the node and its children """
        obj = self.__class__.__new__(self.__class__)
        for name, value in vars(self).items():
            name.startswith("_") or setattr(obj, name, value)
        obj._parent = None
        obj._children = []
        for n in self:
            obj.append(n.copy())
        return obj
            
    def ancestors(self):
        """ climb the tree up over the parents """
        node = self.parent()
        while node:
            yield node
            node = node.parent()

    def previousSibling(self):
        """
        Return the object just before this one in the parent's list of children.
        None if this is the first child, or if we have no parent.
        """
        parent = self.parent()
        if parent:
            i = parent.index(self)
            if i > 0:
                return parent[i-1]

    def nextSibling(self):
        """
        Return the object just after this one in the parent's list of children.
        None if this is the last child, or if we have no parent.
        """
        parent = self.parent()
        if parent:
            i = parent.index(self)
            if i < len(parent) - 1:
                return parent[i+1]

    def previousSiblings(self):
        """
        Iterate (backwards) over the preceding items in our parent's
        list of children.
        """
        node = self.previousSibling()
        while node:
            yield node
            node = self.previousSibling()

    def nextSiblings(self):
        """
        Iterate over the following items in our parent's list of children.
        """
        node = self.nextSibling()
        while node:
            yield node
            node = self.nextSibling()

    def isChildOf(self, otherNode):
        """ find parent in ancestors? """
        for node in self.ancestors():
            if node is otherNode:
                return True
        return False

    def toplevel(self):
        """ returns the toplevel parent Node of this node """
        node = self
        parent = self.parent()
        while parent:
            node = parent
            parent = node.parent()
        return node

    def iterDepthFirst(self, depth = -1):
        """
        Iterate over all the children, and their children, etc.
        Set depth to restrict the search to a certain depth, -1 is unrestricted.
        """
        if depth != 0:
            for i in self:
                yield i
                for j in i.iterDepthFirst(depth - 1):
                    yield j
                
    def iterDepthLast(self, depth = -1):
        """
        Iterate over the children in rings, depth last.
        Set depth to restrict the search to a certain depth, -1 is unrestricted.
        """
        children = self.children()
        while children and depth:
            depth -= 1
            newchildren = []
            for i in children:
                yield i
                newchildren.extend(i.children())
            children = newchildren

    def findChildren(self, cls, depth = -1):
        """
        iterate over all descendants of the current node if they are of
        the class cls or a subclass.
        """
        for node in self.iterDepthLast(depth):
            if isinstance(node, cls):
                yield node

    def findChild(self, cls, depth = -1):
        """
        return the first descendant of the current node of
        the class cls or a subclass, if there is any.
        """
        for node in self.iterDepthLast(depth):
            if isinstance(node, cls):
                return node
    
    def findParent(self, cls):
        """
        find an ancestor of the given class
        """
        for node in self.ancestors():
            if isinstance(node, cls):
                return node


