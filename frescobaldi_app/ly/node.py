# node.py -- Node is a list-like type to build tree structures with
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

The Node class.

(c) 2008-2011 Wilbert Berendsen
License: GPL.

This module contains the Node class that can be used as a simple DOM (Document
Object Model) for building a tree structure.

A Node has children with list-like access methods and keeps also a reference to
its parent. A Node can have one parent; appending a Node to another Node causes
it to be removed from its parent node (if any).

To iterate over the children of a Node:

    for n in node:
        do_something(n)

To get the list of children of a Node:

    children = list(node)

Of course you can get the children directly using:

    child = node[3]

You should inherit from Node to make meaningful tree node types, e.g. to add
custom attributes or multiple sub-types.

A WeakNode class is provided as well, which uses a weak reference to the parent,
so that no cyclic references are created which might improve garbage collection.

"""

import weakref


class Node(object):
    """A list-like class to build tree structures with."""
    __slots__ = ('__weakref__', '_parent', '_children')
    
    def __init__(self, parent=None):
        self._parent = None
        self._children = []
        if parent:
            parent.append(self)

    def _own(self, node):
        """(Internal) Remove node from its parent if any and make us parent."""
        parent = node.parent()
        if parent:
            parent.remove(node)
        node._set_parent(self)
    
    def _set_parent(self, node):
        """(Internal) Set the Node (or None) as our parent."""
        self._parent = node
        
    def parent(self):
        """The parent, or None if the node has no parent."""
        return self._parent

    def index(self, node):
        """Return the index of the given child node."""
        return self._children.index(node)

    def append(self, node):
        """Append a node to the current node.
        
        It will be reparented, that means it will be removed from it's former
        parent if it had one.
        
        """
        self._own(node)
        self._children.append(node)
        
    def extend(self, iterable):
        """Append every Node from iterable."""
        for node in iterable:
            self.append(node)
        
    def insert(self, index, node):
        """Insert a node at the specified index."""
        self._own(node)
        self._children.insert(index, node)
        
    def insert_before(self, other, node):
        """Insert a node before the other node."""
        i = self.index(other)
        self._own(node)
        self._children.insert(i, node)
        
    def remove(self, node):
        """Remove the given child node."""
        self._children.remove(node)
        node._set_parent(None)

    def __nonzero__(self):
        """We are always true."""
        return True
    
    __bool__ = __nonzero__
    
    def __len__(self):
        """Return the number of children."""
        return len(self._children)

    def __getitem__(self, k):
        """Return child at index or children at slice."""
        return self._children[k]

    def __setitem__(self, k, obj):
        """Set child at index or children at slice."""
        old = self._children[k]
        if isinstance(k, slice):
            if k.step:
                # extended slice, number of items must be same
                self._children[k] = obj
                # if this succeeded it's OK
                new = self._children[k]
            else:
                new = tuple(obj)
                self._children[k] = new
            for node in old:
                node._set_parent(None)
            for node in new:
                self._own(node)
        else:
            old._set_parent(None)
            self._children[k] = obj
            self._own(obj)

    def __delitem__(self, k):
        """Delete child at index or children at slice."""
        if isinstance(k, slice):
            for node in self._children[k]:
                node._set_parent(None)
        else:
            self._children[k]._set_parent(None)
        del self._children[k]

    def __contains__(self, node):
        """Return True if the node is our child."""
        return node in self._children

    def clear(self):
        """Remove all children."""
        del self[:]

    def unlink(self):
        """Remove all children and unlink() them as well."""
        for node in self:
            node.unlink()
        del self._children[:]
    
    def replace(self, old, new):
        """Replace a child node with another node."""
        i = self.index(old)
        self[i] = new

    def sort(self, key=None, reverse=False):
        """Sorts the children, optionally using the key function.
        
        Using a key function is recommended, or you must add comparison methods
        to your Node subclass.
        
        """
        self._children.sort(key, reverse=reverse)
        
    def copy(self):
        """Return a deep copy of the node and its children """
        obj = self.__class__.__new__(self.__class__)
        obj._parent = None
        obj._children = []
        self._copy_attrs(obj)
        for n in self:
            obj.append(n.copy())
        return obj
    
    def _copy_attrs(self, node):
        """Called by copy(); copy attributes not starting with '_'."""
        for name, value in vars(self).items():
            name.startswith("_") or setattr(node, name, value)
            
    def ancestors(self):
        """Climb the tree up over the parents."""
        node = self.parent()
        while node:
            yield node
            node = node.parent()

    def previous_sibling(self):
        """Return the sibling object just before us in our parents list.
        
        Returns None if this is the first child, or if we have no parent.
        
        """
        for i in self.backward():
            return i

    def next_sibling(self):
        """Return the sibling object just after us in our parents list.
        
        Returns None if this is the last child, or if we have no parent.
        
        """
        for i in self.forward():
            return i

    def backward(self):
        """Iterate (backwards) over the preceding siblings."""
        parent = self.parent()
        if parent:
            i = parent.index(self)
            return iter(parent[i-1::-1])

    def forward(self):
        """Iterate over the following siblings."""
        parent = self.parent()
        if parent:
            i = parent.index(self)
            return iter(parent[i+1::])

    def is_descendant_of(self, parent):
        """Return True if self is a descendant of parent, else False."""
        for n in self.ancestors():
            if n is parent:
                return True
        return False

    def toplevel(self):
        """Return the toplevel parent Node of this node."""
        node = self
        parent = self.parent()
        while parent:
            node = parent
            parent = node.parent()
        return node
    
    def descendants(self, depth = -1):
        """Yield all the descendants, in tree order. Same as iter_depth()."""
        return self.iter_depth(depth)
    
    def iter_depth(self, depth = -1):
        """Iterate over all the children, and their children, etc.
        
        Set depth to restrict the search to a certain depth, -1 is unrestricted.
        
        """
        if depth != 0:
            for i in self:
                yield i
                for j in i.iter_depth(depth - 1):
                    yield j
                
    def iter_rings(self, depth = -1):
        """Iterate over the children in rings, depth last.
        
        This method returns the closest descendants first.
        Set depth to restrict the search to a certain depth, -1 is unrestricted.
        
        """
        children = list(self)
        while children and depth:
            depth -= 1
            newchildren = []
            for i in children:
                yield i
                newchildren.extend(i)
            children = newchildren

    def find(self, cls, depth = -1):
        """Yield all descendants if they are an instance of cls.
        
        cls may also be a tuple of classes. This method uses iter_depth().
        
        """
        for node in self.iter_depth(depth):
            if isinstance(node, cls):
                yield node
        
    def find_children(self, cls, depth = -1):
        """Yield all descendants if they are an instance of cls.
        
        cls may also be a tuple of classes. This method uses iter_rings().
        
        """
        for node in self.iter_rings(depth):
            if isinstance(node, cls):
                yield node

    def find_child(self, cls, depth = -1):
        """Return the first descendant that's an instance of cls.
        
        cls may also be a tuple of classes. This method uses iter_rings().
        
        """
        for node in self.iter_rings(depth):
            if isinstance(node, cls):
                return node
    
    def find_parent(self, cls):
        """Find an ancestor that's an instance of the given class.
        
        cls may also be a tuple of classes.
        
        """
        for node in self.ancestors():
            if isinstance(node, cls):
                return node
    
    def dump(self):
        """Return a string representation of the tree."""
        def line(obj, indent):
            yield indent * "  " + repr(obj)
            for c in obj:
                for l in line(c, indent + 1):
                    yield l
        return '\n'.join(line(self, 0))



class WeakNode(Node):
    """A Node type using a weak reference to the parent."""
    __slots__ = ()
    def _set_parent(self, node):
        self._parent = None if node is None else weakref.ref(node)
    
    def parent(self):
        """The parent, or None if the node has no parent."""
        if self._parent is not None:
            return self._parent()


