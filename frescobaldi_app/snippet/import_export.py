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
Import and export of snippets.
"""

from __future__ import unicode_literals

import sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app

from . import snippets


def save(names, filename):
    """Saves the named snippets to a file."""
    root = ET.Element('snippets')
    root.text = root.tail = '\n'
    d = ET.ElementTree(root)
    
    for name in names:
        s = ET.Element('snippet')
        s.set('id', name)
        s.text = s.tail = '\n'
        
        title = ET.Element('title')
        title.text = snippets.title(name, False)
        title.tail = '\n'
        
        body = ET.Element('body')
        body.text = snippets.text(name)
        body.tail = '\n'
        
        s.append(title)
        s.append(body)
        root.append(s)
    d.write(filename, "UTF-8")


def load(filename, widget):
    """Loads snippets from a file, displaying them in a list.
    
    The user can then choose:
    - overwrite builtin snippets or not
    - overwrite own snippets with same title or not
    - select and view snippets contents.
    
    """
    try:
        d = ET.parse(filename)
        l = list(d.findall('snippet'))
        if not l:
            raise ValueError(_("No snippets found."))
    except Exception as e:
        QMessageBox.critical(widget, app.caption(_("Error")),
        _("Can't load {url}\n\n{error}").format(
            url=filename, error=e))
        return




