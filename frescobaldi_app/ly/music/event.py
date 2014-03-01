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


class Events(object):
    """Traverses a music tree and records music events from it."""
    unfold_repeats = False
    
    def read(self, node, time=0, scaling=1):
        """Read events from the node and all its child nodes; return time."""
        return self.traverse(node, time, scaling)
    
    def traverse(self, node, time, scaling):
        """Traverse node and call event handlers; record and return the time."""
        return node.events(self, time, scaling)


