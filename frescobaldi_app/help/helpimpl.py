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

all_pages = {}


class helpmeta(type):
    """Makes all methods classmethod or staticmethod and adds name attribute.
    
    Also adds each class (which is in fact a help page) to the all_pages dict.
    
    """
    def __new__(cls, name, bases, d):
        for n in ('title', 'body', 'children', 'seealso'):
            if n in d:
                meth = (staticmethod, classmethod)[d[n].func_code.co_argcount]
                d[n] = meth(d[n])
        d['name'] = name
        page = type.__new__(cls, name, bases, d)
        all_pages[name] = page
        return page


class help_page(object):
    """Base class for help items.
    
    classes based on help are never instantiated; the class is simply used as a
    data container. Some methods should be defined, which are used as classmethod
    if they have an argument, or as staticmethod when they accept no arguments.
    
    The methods may return translated text, when the application changes
    language, the methods are called again.
    
    Set the popup class attribute to True to make the help topic a popup.
    """
    popup = False
    
    def title():
        return ""
    
    def body():
        return ""
    
    def children():
        return ()
    
    def seealso():
        return ()


# This syntax to make help use the metaclass works in both Python2 and 3
help_page = helpmeta('help_page', help_page.__bases__, dict(help_page.__dict__))

