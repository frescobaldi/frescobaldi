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
        
        # insert the snippet, might return a new cursor
        if 'python' in variables:
            new = insert_python(text, cursor)
        else:
            new = insert_snippet(text, cursor)
        
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
    view.setTextCursor(new or cursor)


def insert_snippet(text, cursor):
    """Inserts a normal text snippet.
    
    After the insert, the cursor points to the end of the inserted snippet.
    
    If this function returns a cursor it must be set as the cursor for the view
    after the snippet has been inserted.
    
    """
    exp_base = expand.ExpanderBasic(cursor)
    
    ANCHOR, CURSOR, SELECTION, SELECTION_WS = 1, 2, 3, 4 # just some constants
    evs = [] # make a list of events, either text or a constant
    for text, key in snippets.expand(text):
        if text:
            evs.append(text)
        if key == '$':
            evs.append('$')
        elif key:
            # basic variables
            func = getattr(exp_base, key, None)
            if func:
                evs.append(func())
            elif key == 'SELECTION':
                evs.append(SELECTION if cursor.hasSelection() else CURSOR)
            elif key == 'SELECTION_WS':
                evs.append(SELECTION_WS if cursor.hasSelection() else CURSOR)
            elif key == 'C':
                evs.append(CURSOR)
            elif key == 'A':
                evs.append(ANCHOR)
    # do the padding if SELECTION_WS is used
    try:
        i = evs.index(SELECTION_WS)
    except ValueError:
        if SELECTION not in evs:
            cursor.removeSelectedText()
    else:
        cursortools.stripSelection(cursor)
        space = '\n' if '\n' in cursor.selection().toPlainText() else ' '
        if i > 0:
            evs[i-1] = evs[i-1].rstrip() + space
        if i < len(evs) - 1:
            evs[i+1] = space + evs[i+1].lstrip()
    # now insert the text
    ins = QTextCursor(cursor)
    ins.setPosition(cursor.selectionStart())
    a, c = -1, -1
    for e in evs:
        if e == ANCHOR:
            a = ins.position()
        elif e == CURSOR:
            c = ins.position()
        elif e in (SELECTION, SELECTION_WS):
            ins.setPosition(cursor.selectionEnd())
        else:
            ins.insertText(e)
    cursor.setPosition(ins.position())
    # return a new cursor if requested
    if (a, c) != (-1, -1):
        new = QTextCursor(cursor)
        if a != -1:
            new.setPosition(a)
        if c != -1:
            new.setPosition(c, QTextCursor.KeepAnchor if a != -1 else QTextCursor.MoveAnchor)
        return new


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




