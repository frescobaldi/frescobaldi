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
Insert snippets into a Document.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings

import tokeniter

from . import snippets



def insert(name, view):
    """Insert named snippet into the view."""
    text, variables = snippets.get(name)
    
    cursor = view.textCursor()
    
    exp_base = ExpanderBasic(view)
    
    with tokeniter.editBlock(cursor):
        for text, key in snippets.expand(text):
            if text:
                cursor.insertText(text)
            if key == "$":
                cursor.insertText(key)
            elif key:
                # basic variables
                func = getattr(exp_base, key, None)
                if func:
                    cursor.insertText(func())
                    continue




class ExpanderBasic(object):
    """Expands basic variables."""
    def __init__(self, view):
        self.view = view
    
    def LILYPOND_VERSION(self):
        import lilypondinfo
        return lilypondinfo.preferred().versionString



