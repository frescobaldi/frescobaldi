# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 by Wilbert Berendsen
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
Information about grobs (Graphical Objects).
"""

import itertools

from . import interfaces as _interfaces

def properties(grob):
    """Returns the list of properties the named grob supports."""
    return sorted(sum(itertools.chain(
        _interfaces.interfaces[i] for i in _interfaces.grobs.get(grob, [])), []))

def interfaces(grob):
    """Returns the list of interfaces a grob supports."""
    return _interfaces.grobs.get(grob, [])

def interface_properties(iface):
    """Retrns the list of properties an interface supports."""
    return _interfaces.interfaces.get(iface, [])

def properties_with_interface(grob):
    """Returns a list of two-tuples (property, interface)."""
    return sorted(
        (p, i)
        for i in _interfaces.grobs.get(grob, [])
        for p in _interfaces.interfaces[i])

def interfaces_for_property(prop):
    """(Expensive) returns the list of interfaces that define the property.
    
    Most times returns one, but several interface names may be returned.
    
    """
    return [iface
        for iface, props in _interfaces.interfaces.items()
        if prop in props]

