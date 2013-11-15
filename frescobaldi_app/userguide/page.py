# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
Page, a page from the Frescobaldi User Manual.
"""

from __future__ import unicode_literals

import string

import simplemarkdown

from . import read
from . import resolve


class Page(object):
    def __init__(self, name=None):
        self._children = []
        self._title = None
        self._attrs = None
        
        if name:
            self.load(name)
    
    def load(self, name):
        doc, attrs = read.document(name)
        self.parse_text(doc, attrs)
        
    def parse_text(self, text, attrs=None):
        self._attrs = attrs or {}
        t = self._tree = simplemarkdown.Tree()
        # parse and translate the document
        read.Parser().parse(text, t)
        # resolve variables...
        variables = self._attrs.get('VARS')
        d = self._variables = {}
        if variables:
            for v in variables:
                name, type, text = v.split(None, 2)
                d[name] = (type, text)
        
        fmt = string.Formatter().vformat
        func = self.resolve
        class Resolve(dict):
            def __getitem__(self, name):
                return func(name)
        resolver = Resolve()
        for e in t.find('inline_text'):
            s = e.args[0]
            n = fmt(s, (), resolver)
            e.args = (n,)
    
    def resolve(self, name):
        """Return the value for the variable.
        
        First the #VARS section is consulted, then the general methods in 
        the resolve module.
        
        """
        try:
            type, text = self._variables[name]
        except KeyError:
            try:
                return getattr(resolve, name)()
            except AttributeError:
                return "[undefined]"
        if type == "url":
            return text #TODO: make clickable
        else:
            return text
        

    def is_popup(self):
        """Return True if the helppage should be displayed as a popup."""
        try:
            return 'popup' in self._attrs['PROPERTIES']
        except KeyError:
            return False
    
    def title(self):
        """Return the title"""
        for heading in self._tree.find('heading'):
            return ''.join(e.args[0] for e in self._tree.find('inline_text', heading))
    
    def body(self):
        """Return the HTML body."""
        return self._tree.html()
        
    def children(self):
        """Return the list of names of child documents."""
        return self._attrs.get("SUBDOCS") or []
    
    def seealso(self):
        """Return the list of names of "see also" documents."""
        return self._attrs.get("SEEALSO") or []


