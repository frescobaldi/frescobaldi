# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2010 - 2019 by Wilbert Berendsen
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
Manages lists of rectangular objects and quickly finds them.
"""

import bisect
import operator


Left   = 0
Top    = 1
Right  = 2
Bottom = 3


class Rectangles:
    """
    Manages a list of rectangular objects and quickly finds objects at
    some point, in some rectangle or intersecting some rectangle.

    The implementation uses four lists of the objects sorted on either
    coordinate, so retrieval is fast.

    Bulk adding is done in the constructor or via the bulk_add() method (which
    clears the indexes, that are recreated on first search).  Single objects
    can be added and deleted, keeping the indexes, but that's slower.

    You should inherit from this class and implement the method get_coords(obj)
    to get the rectangle of the object (x, y, x2, y2). These are requested only
    once. x should be < x2 and y should be < y2.

    """
    def __init__(self, objects=None):
        """Initializes the Rectangles object.

        objects should, if given, be an iterable of rectangular objects, and
        bulk_add() is called on those objects.

        """
        self._items = {} # maps object to the result of func(object)
        self._index = {} # maps side to indices, objects (index=coordinate of that side)
        if objects:
            self.bulk_add(objects)

    def get_coords(self, obj):
        """You should implement this method.

        The result should be a four-tuple with the coordinates of the rectangle
        the object represents (x, y, x2, y2). These are requested only once.
        x should be < x2 and y should be < y2.

        """
        return (0, 0, 0, 0)

    def add(self, obj):
        """Adds an object to our list. Keeps the index intact."""
        if obj in self._items:
            return
        self._items[obj] = coords = self.get_coords(obj)
        for side, (indices, objects) in self._index.items():
            i = bisect.bisect_left(indices, coords[side])
            indices.insert(i, coords[side])
            objects.insert(i, obj)

    def bulk_add(self, objects):
        """Adds many new items to the index using the function given in the constructor.

        After this, the index is cleared and recreated on the first search operation.

        """
        self._items.update((obj, self.get_coords(obj)) for obj in objects)
        self._index.clear()

    def remove(self, obj):
        """Removes an object from our list. Keeps the index intact."""
        del self._items[obj]
        for indices, objects in self._index.values():
            i = objects.index(obj)
            del objects[i]
            del indices[i]

    def clear(self):
        """Empties the list of items."""
        self._items.clear()
        self._index.clear()

    def at(self, x, y):
        """Returns a set() of objects that are touched by the given point."""
        return self._test(
            (self._smaller, Top, y),
            (self._larger, Bottom, y),
            (self._smaller, Left, x),
            (self._larger, Right, x))

    def inside(self, left, top, right, bottom):
        """Returns a set() of objects that are fully in the given rectangle."""
        return self._test(
            (self._larger, Top, top),
            (self._smaller, Bottom, bottom),
            (self._larger, Left, left),
            (self._smaller, Right, right))

    def intersecting(self, left, top, right, bottom):
        """Returns a set() of objects intersecting the given rectangle."""
        return self._test(
            (self._smaller, Top, bottom),
            (self._larger, Bottom, top),
            (self._smaller, Left, right),
            (self._larger, Right, left))

    def width(self, obj):
        """Return the width of the specified object.

        This can be used for sorting a set returned by at(), inside() or
        intersecting(). For example::

            for r in sorted(rects.at(10, 20), key=rects.width):
                # ...

        """
        coords = self._items[obj]
        return coords[Right] - coords[Left]

    def height(self, obj):
        """Return the height of the specified object. See also width()."""
        coords = self._items[obj]
        return coords[Bottom] - coords[Top]

    def closest(self, obj, side):
        """Returns the object closest to the given one, going to the given side."""
        coords = self._items[obj]
        pos = coords[side^2]
        lat = (coords[side^1|2] - coords[side^1&2]) / 2.0
        direction = -1 if side < Right else 1
        indices, objects = self._sorted(side^2)
        i = objects.index(obj)
        mindist = indices[-1]
        result = []
        for other in objects[i+direction::direction]:
            coords = self._items[other]
            pos1 = coords[side^2]
            d = abs(pos1 - pos)
            if d > mindist:
                break
            lat1 = (coords[side^1|2] - coords[side^1&2]) / 2.0
            dlat = abs(lat1 - lat)
            if dlat < d:
                dist = dlat + d  # manhattan dist
                result.append((other, dist))
                mindist = min(mindist, dist)
        if result:
            result.sort(key=lambda r: r[1])
            return result[0][0]

    def nearest(self, x, y):
        """Return the object with the shortest distance to the point x, y.

        The point (x, y) is outside the object. Use at() to get objects that
        touch the point (x, y). If there are no objects, None is returned.

        """
        i = self._items

        left = self._larger(Left, x)            # closest one is first
        right = self._smaller(Right, x)         # closest one is last
        top = self._larger(Top, y)              # closest one is first
        bottom = self._smaller(Bottom, y)       # closest one is last

        result = []

        # first find adjacent rectangles. For each side, as soon as one is
        # found, don't look further for that side. Only save rectangles that are
        # closer but not adjacent, they could be closer on another side.
        left_over = 0
        for o in left:
            if o not in top and o not in bottom:
                result.append((i[o][Left] - x, o))
                break
            left_over += 1
        top_over = 0
        for o in top:
            if o not in left and o not in right:
                result.append((i[o][Top] - y, o))
                break
            top_over += 1
        right_over = 0
        for o in right[::-1]:
            if o not in top and o not in bottom:
                result.append((x - i[o][Right], o))
                break
            right_over -= 1
        bottom_over = 0
        for o in bottom[::-1]:
            if o not in left and o not in right:
                result.append((y - i[o][Bottom], o))
                break
            bottom_over -= 1
        # at most 4 rectangles are found, the closest one on each edge.
        # Now look for rectangles that could be closer at the corner.
        if left_over and top_over:
            for o in set(left[:left_over]).intersection(top[:top_over]):
                result.append((i[o][Left] - x + i[o][Top] - y, o))
        if top_over and right_over:
            for o in set(top[:top_over]).intersection(right[right_over:]):
                result.append((i[o][Top] - y + x - i[o][Right], o))
        if left_over and bottom_over:
            for o in set(left[:left_over]).intersection(bottom[bottom_over:]):
                result.append((i[o][Left] - x + y - i[o][Bottom], o))
        if bottom_over and right_over:
            for o in set(bottom[bottom_over:]).intersection(right[right_over:]):
                result.append((y - i[o][Bottom] + x - i[o][Right], o))

        if result:
            return min(result, key=operator.itemgetter(0))[1]

    def __len__(self):
        """Return the number of objects."""
        return len(self._items)

    def __contains__(self, obj):
        """Return True if the object is managed by us."""
        return obj in self._items

    def __bool__(self):
        """Always return True."""
        return True

    def __iter__(self):
        """Iterate over the objects in undefined order."""
        return iter(self._items)

    # private helper methods
    def _test(self, *tests):
        """Performs tests and returns objects that fulfill all of them.

        Every test should be a three tuple(method, side, value).
        Method is either self._smaller or self._larger.
        Returns a (possibly empty) set.

        """
        meth, side, value = tests[0]
        result = set(meth(side, value))
        if result:
            for meth, side, value in tests[1:]:
                result &= set(meth(side, value))
                if not result:
                    break
        return result

    def _smaller(self, side, value):
        """Returns objects for side below value."""
        indices, objects = self._sorted(side)
        i = bisect.bisect_right(indices, value)
        return objects[:i]

    def _larger(self, side, value):
        """Returns objects for side above value."""
        indices, objects = self._sorted(side)
        i = bisect.bisect_left(indices, value)
        return objects[i:]

    def _sorted(self, side):
        """Returns a two-tuple (indices, objects) sorted on index for the given side."""
        try:
            return self._index[side]
        except KeyError:
            if self._items:
                objects = [(coords[side], obj) for obj, coords in self._items.items()]
                objects.sort(key=operator.itemgetter(0))
                result = tuple(map(list, zip(*objects)))
            else:
                result = [], []
            self._index[side] = result
            return result


