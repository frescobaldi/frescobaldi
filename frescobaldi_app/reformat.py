# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Reformat the selection or the whole document, only adjusting whitespace.

What it does:

- remove trialing whitespace

- newline after all { or << in lilypond mode, unless terminated on same line
- same way newline before >> or }

- newline before and after many non-postfix commands, such as \set, \override
- at least one blank line between multiline top-level blocks (unless comment)

- wordwrap lines longer than 79 characters

- remove indent for commented lines with more than two comment characters

- Html, scheme, strings, etc are left alone
- Never removes existing newlines

"""

from __future__ import unicode_literals

from PyQt4.QtGui import QTextCursor

import cursortools
import tokeniter
import indent
import ly.lex.lilypond
import ly.lex.scheme


def get_blocks(cursor):
    """Yields all or the selected blocks."""
    if cursor.hasSelection():
        return cursortools.blocks(cursor) 
    else:
        return cursortools.all_blocks(cursor.document())


def reformat(cursor):
    """Reformats the selection or the whole document, adjusting the whitespace."""
    def newlinebefore(t):
        editor.insertText(tokeniter.cursor(block, t, end=0), '\n')
    
    def newlineafter(t):
        editor.insertText(tokeniter.cursor(block, t, start=len(t)), '\n')
    
    indent_vars = indent.indent_variables(cursor.document())
    
    with cursortools.compress_undo(cursor):
        indent.re_indent(cursor)
        with cursortools.Editor() as editor:
            for block in get_blocks(cursor):
                
                denters = []
                tokens = tokeniter.tokens(block)
                
                nonspace_index = -1
                for i, t in enumerate(tokens):
                    if isinstance(t, ly.lex.Indent) and t in ('{', '<<'):
                        denters.append(i)
                    elif isinstance(t, ly.lex.Dedent) and t in ('}', '>>'):
                        if denters:
                            denters.pop()
                        elif nonspace_index != -1:
                            newlinebefore(t)
                    elif not isinstance(t, ly.lex.Space):
                        nonspace_index = i
                for i in denters:
                    if i < nonspace_index:
                        newlineafter(tokens[i])
                    
                # TODO: wrap long lines
        
        indent.re_indent(cursor)
        
        # move commented lines with more than 2 comment characters
        # to column 0
        with cursortools.Editor() as editor:
            for block in get_blocks(cursor):
                tokens = tokeniter.tokens(block)
                if (len(tokens) == 2
                    and isinstance(tokens[0], ly.lex.Space)
                    and isinstance(tokens[1], (
                        ly.lex.lilypond.LineComment,
                        ly.lex.scheme.LineComment))
                    and len(tokens[1]) > 2
                    and len(set(tokens[1][:3])) == 1):
                    editor.removeSelectedText(tokeniter.cursor(block, tokens[0]))
        
        remove_trailing_whitespace(cursor)


def remove_trailing_whitespace(cursor):
    """Removes whitespace from all lines in the cursor's selection.
    
    If there is no selection, the whole document is used.
    
    """
    ranges = []
    for block in get_blocks(cursor):
        length = len(block.text())
        strippedlength = len(block.text().rstrip())
        if strippedlength < length:
            ranges.append((block.position() + strippedlength, block.position() + length))
    if ranges:
        c = QTextCursor(cursor)
        with cursortools.compress_undo(c):
            for start, end in reversed(ranges):
                c.setPosition(start)
                c.setPosition(end, QTextCursor.KeepAnchor)
                c.removeSelectedText()

