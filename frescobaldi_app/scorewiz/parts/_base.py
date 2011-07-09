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
Base types for parts.
"""

import __builtin__
import collections

import icons


# A Category is simply a named tuple with default values.
# The title is callable because the program supports dynamic language change.
Category = collections.namedtuple("Category", "title items icon")(
    title = lambda: '',
    items = [],
    icon = icons.get("folder-open")
)._replace



class Part(object):
    """Base class for Parts."""
    @staticmethod
    def title(_=__builtin__._):
        """Should return a title.
        
        If a translator is given, it is used instead of the builtin.
        
        """
    
    @staticmethod
    def short(_=__builtin__._):
        """Should return an abbreviated title.
        
        If a translator is given, it is used instead of the builtin.
        
        """


