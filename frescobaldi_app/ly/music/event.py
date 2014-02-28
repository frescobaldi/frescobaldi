# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2014 - 2014 by Wilbert Berendsen
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
Translates a music.items.Document tree into lists of events.

"""

from __future__ import unicode_literals

import itertools

from . import items


class Events(object):
    """Traverses a music tree and records music events from it."""
    unfold_repeats = False
    
    def __init__(self):
        self.iter = iter
    
    def read(self, node, time=0, scaling=1):
        """Read events from the node and all its child nodes; return time."""
        return self.traverse(node, time, scaling)
    
    def traverse(self, node, time, scaling):
        """Traverse node and call event handlers; record and return the time."""
        return node.events(self, time, scaling)


class TimePosition(Events):
    """Traverses a music tree and records music events from it.
    
    This class can stop at a certain condition, which is tested with every node.
    
    """
    def __init__(self, quit_predicate=None):
        self.keep_going = True
        self.time = None
        if quit_predicate:
            predicate = lambda node: self.keep_going
            self.iter = lambda node: itertools.takewhile(predicate, node)
            self.quit_predicate = quit_predicate
        else:
            self.iter = iter
            self.quit_predicate = lambda node: False
    
    def read(self, node, time=0, scaling=1):
        """Read events from the node and all its child nodes; return time."""
        time = self.traverse(node, time, scaling)
        return time if self.time is None else self.time
    
    def traverse(self, node, time, scaling):
        """Traverse node and call event handlers; record and return the time."""
        if self.keep_going:
            if self.quit_predicate(node):
                self.keep_going = False
                self.time = time
            else:
                time = node.events(self, time, scaling)
        return time


