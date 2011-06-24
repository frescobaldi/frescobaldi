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
from PyQt4.QtGui import QTextCursor

import cursortools
import indent
import tokeniter

from . import snippets
from . import expand


def insert(name, view):
    """Insert named snippet into the view."""
    text, variables = snippets.get(name)
    
    cursor = view.textCursor()
    
    block = cursor.document().findBlock(cursor.selectionStart())
    with cursortools.editBlock(cursor):
        
        # insert the snippet
        if 'python' in variables:
            insert_python(text, cursor)
        else:
            insert_snippet(text, cursor)
        
        # QTextBlock the snippet ends
        last = cursor.block()
        
        # re-indent if not explicitly suppressed by a 'no-indent' variable
        if last != block and 'no-indent' not in variables:
            tokeniter.update(block) # tokenize inserted lines
            while True:
                block = block.next()
                if indent.setIndent(block, indent.computeIndent(block)):
                    tokeniter.update(block)
                if block == last:
                    break
    view.setTextCursor(cursor)

def insert_snippet(text, cursor):
    """Inserts a normal text snippet.
    
    After the insert, the cursor points to the end of the inserted snippet.
    
    """
    exp_base = expand.ExpanderBasic(cursor)
    
    text1, text2 = [], []
    t = text1
    
    for text, key in snippets.expand(text):
        if text:
            t.append(text)
        if key == "$":
            t.append('$')
        elif key:
            # basic variables
            func = getattr(exp_base, key, None)
            if func:
                t.append(func())
                continue
            if key == 'SELECTION':
                t = text2
            elif key == 'SELECTION_WS':
                cursortools.stripSelection(cursor)
                space = '\n' if '\n' in cursor.selection().toPlainText() else ' '
                t.append(space)
                t = text2
                t.append(space)
    cur1 = QTextCursor(cursor)
    cur1.setPosition(cursor.selectionStart())
    cur2 = QTextCursor(cursor)
    cur2.setPosition(cursor.selectionEnd())
    cur1.insertText(''.join(text1))
    cur2.insertText(''.join(text2))
    cursor.setPosition(cur2.position())


def insert_python(text, cursor):
    """Regards the text as Python code, and exec it.
    
    the following variables are available:
    
    - text: contains selection or '', set it to insert new text

    After the insert, the cursor points to the end of the inserted snippet.
    
    """
    code = compile(text, "<snippet>", "exec")
        
    namespace = {
        'text': cursor.selection().toPlainText(),
    }
    exec code in namespace
    cursor.insertText(namespace['text'])




