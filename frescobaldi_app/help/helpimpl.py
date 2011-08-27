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
The help contents definition.
"""

class helpmeta(type):
    """Makes all methods static and adds name attribute."""
    def __new__(cls, name, bases, d):
        for n in d:
            d[n] = staticmethod(d[n])
        d['name'] = name
        return type.__new__(cls, name, bases, d)


class help(object):
    """Base class for help items.
    
    classes based on help are never instantiated; the class is simply used as a
    data container. Some methods should be defined, which are used static.
    
    The methods may return translated text, when the application changes
    language, the methods are called again.
    
    """
    def title():
        return ""
    
    def body():
        return ""
    
    def children():
        return ()
    
    def seealso():
        return ()


# This syntax to make help use the metaclass works in both Python2 and 3
help = helpmeta('help', help.__bases__, dict(help.__dict__))

