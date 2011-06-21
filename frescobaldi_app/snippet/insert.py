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
from . import expand


def insert(name, view):
    """Insert named snippet into the view."""
    text, variables = snippets.get(name)
    
    cursor = view.textCursor()
    
    with tokeniter.editBlock(cursor):
        if 'python' in variables:
            insert_python(text, cursor)
        else:
            insert_snippet(text, cursor)
        

def insert_snippet(text, cursor):
    """Inserts a normal text snippet."""
    exp_base = expand.ExpanderBasic(cursor)
    
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


def insert_python(text, cursor):
    """Regards the text as Python code, and exec it.
    
    the following variables are available:
    
    - text: contains selection or '', set it to insert new text

    """
    code = compile(text, "<snippet>", "exec")
        
    namespace = {
        'text': cursor.selection().toPlainText(),
    }
    exec code in namespace
    cursor.insertText(namespace['text'])




