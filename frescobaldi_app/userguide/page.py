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

import simplemarkdown

from . import read

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
        
    def parse_text(text, attrs=None):
        self._attrs = attrs or {}
        t = simplemarkdown.Tree()
        read.Parser().parse(text, t)
        # resolve variables...
    
    def title(self):
        """Return the title"""
    
    def body(self):
        """Return the HTML body."""
    
    def children(self):
        """Return the list of names of child documents."""
        return self._attrs.get("SUBDOCS") or []
    
    def seealso(self):
        """Return the list of names of "see also" documents."""
        return self._attrs.get("SEEALSO") or []


