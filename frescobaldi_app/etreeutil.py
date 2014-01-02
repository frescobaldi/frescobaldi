# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
Utility functions for use with xml.etree.ElementTree.
"""

from __future__ import unicode_literals


def isblank(s):
    """Return True if s is empty or whitespace only."""
    return not s or s.isspace()


def indent(elem, indent_string="  ", level=0):
    """Indent the XML in element.
    
    Text content that is already non-whitespace is not changed.
    
    """
    # based on http://effbot.org/zone/element-lib.htm#prettyprint
    i = "\n" + indent_string * level
    if len(elem):
        if isblank(elem.text):
            elem.text = i + indent_string
        if isblank(elem.tail):
            elem.tail = i
        for elem in elem:
            indent(elem, indent_string, level+1)
        if isblank(elem.tail):
            elem.tail = i
    else:
        if level and isblank(elem.tail):
            elem.tail = i


