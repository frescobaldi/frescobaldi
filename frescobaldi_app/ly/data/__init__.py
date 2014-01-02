# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Query functions to get data from the LilyPond-generated _data.py module.
"""

def grob_properties(grob):
    """Returns the list of properties the named grob supports."""
    from . import _data
    return sorted(uniq(prop
        for iface in _data.grobs.get(grob, [])
        for prop in _data.interfaces[iface]))

def grob_properties_with_interface(grob):
    """Returns a list of two-tuples (property, interface)."""
    from . import _data
    return sorted(
        (prop, iface)
        for iface in _data.grobs.get(grob, [])
        for prop in _data.interfaces[iface])

def grob_interfaces(grob, prop=None):
    """Returns the list of interfaces a grob supports.
    
    If prop is given, only returns the interfaces that define prop.
    
    """
    from . import _data
    ifaces = _data.grobs.get(grob, [])
    if prop is None:
        return ifaces
    return [iface for iface in ifaces
            if prop in grob_interface_properties(iface)]

def grob_interface_properties(iface):
    """Returns the list of properties an interface supports."""
    from . import _data
    return _data.interfaces.get(iface, [])

def grob_interfaces_for_property(prop):
    """Returns the list of interfaces that define the property.
    
    Most times returns one, but several interface names may be returned.
    
    """
    from . import _data
    return [iface
        for iface, props in _data.interfaces.items()
        if prop in props]

def grobs():
    """Returns the sorted list of all grob names."""
    from . import _data
    return sorted(_data.grobs.keys())
    
def all_grob_properties():
    """Returns the list of all properties."""
    from . import _data
    return sorted(uniq(sum(_data.interfaces.values(), [])))

def context_properties():
    """Returns the list of context properties."""
    from . import _data
    return _data.contextproperties

def engravers():
    """Returns the list of engravers and performers."""
    from . import _data
    return _data.engravers

def music_glyphs():
    """Returns the list of glyphs in the emmentaler font."""
    from . import _data
    return _data.musicglyphs

def scheme_keywords():
    """Returns the list of guile keywords."""
    from . import _data
    return _data.scheme_keywords

def scheme_functions():
    """Returns the list of scheme functions."""
    from . import _data
    return _data.scheme_functions

def scheme_variables():
    """Returns the list of scheme variables."""
    from . import _data
    return _data.scheme_variables

def scheme_constants():
    """Returns the list of scheme constants."""
    from . import _data
    return _data.scheme_constants

def all_scheme_words():
    """Returns the list of all scheme words."""
    from . import _data
    return _data.scheme_keywords + _data.scheme_functions \
        + _data.scheme_variables + _data.scheme_constants

def uniq(iterable):
    """Returns an iterable, removing duplicates. The items should be hashable."""
    s, l = set(), 0
    for i in iterable:
        s.add(i)
        if len(s) > l:
            yield i
            l = len(s)


