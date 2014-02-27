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
    
    def event(self, node, time, scaling):
        """Called for every node.
        
        By default this method does nothing. If you reimplement it and
        return a time value, the normal event processing is not done (it is
        expected that you traverse the child nodes yourself then).
        
        If you use a quit_predicate, this method is not called when that
        returns True. (quit() is then called.)
        
        """
    
    def quit(self, node, time, scaling):
        """Called when the quit_predicate returned True."""
    
    def traverse(self, node, time, scaling):
        """Traverse node and call event handlers; record and return the time."""
        if self.keep_going:
            if self.quit_predicate(node):
                self.keep_going = False
                self.time = time
                self.quit(node, time, scaling)
            else:
                res = self.event(node, time, scaling)
                if res is None:
                    if isinstance(node, items.Durable):
                        time += node.length() * scaling
                    elif isinstance(node, items.UserCommand):
                        time = self.handle_user_command(node, time, scaling)
                    elif isinstance(node, items.MusicList) and node.simultaneous:
                        time = max(self.traverse(n, time, scaling) for n in self.iter(node))
                    elif isinstance(node, items.Music):
                        if isinstance(node, items.Grace):
                            scaling = 0
                        elif isinstance(node, items.Scaler):
                            scaling *= node.scaling
                        for n in self.iter(node):
                            time = self.traverse(n, time, scaling)
                else:
                    time += res
        return time

    def handle_user_command(self, node, time, scaling):
        """Handle a UserCommand; by default just adds the length."""
        return time + node.length() * scaling


