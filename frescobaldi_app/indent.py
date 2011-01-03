# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Indent and auto-indent.
"""

from PyQt4.QtGui import QTextCursor

import ly.tokenize
import tokeniter


INDENT_WIDTH = 2
TAB_WIDTH = 8
ALLOW_TABS = False

# scheme commands that can have one argument on the same line and then want the next arguments
# on the next lines at the same position.
scheme_sync_args = (
    'if', 'and', 'or', 'set!',
    '=', '<', '<=', '>', '>=',
    'eq?', 'eqv?', 'equal?',
    'filter',
)


def autoIndentBlock(block):
    """Auto-indents the given block."""
    setIndent(block, computeIndent(block))


def computeIndent(block):
    """Returns the indent the given block should have."""
    
    # count the dedent tokens at the beginning of the block
    indents = 0
    for token in tokeniter.tokens(block):
        # dont dedent scheme dedent tokens at beginning of lines (unusual)
        if isinstance(token, ly.tokenize.Dedent) and not isinstance(token, ly.tokenize.scheme.CloseParen):
            indents -= 1
        elif not isinstance(token, ly.tokenize.Space):
            break

    # these variables control the position (yet to be translated to tabbed (real) columns)
    # and how much to add
    indent_pos = None
    indent_add = 0
    
    # look backwards for the token that starts this indent
    prev = block.previous()
    while prev.isValid():
        
        # skip empty blocks
        if prev.length() <= 1:
            prev = prev.previous()
            continue
        
        closers = 0
        found = False
        lasttokens = []
        
        it = tokeniter.TokenIterator(prev, atEnd=True)
        token = None # in case of empty line
        for token in it.backward(False):
            if isinstance(token, ly.tokenize.Dedent):
                indents -= 1
                if isinstance(token, ly.tokenize.scheme.CloseParen):
                    closers = 0 # scheme close parens are not moved
                else:
                    closers += 1
            elif isinstance(token, ly.tokenize.Indent):
                indents += 1
                closers = 0
                if not found:
                    if indents == 1:
                        found = it.copy()
                    else:
                        lasttokens.append(token)
            elif not isinstance(token, ly.tokenize.Space):
                closers = 0
                if not found:
                    lasttokens.append(token)
        
        if found:
            # the token that started the current indent has been found
            # if there are no tokens after the indent-opener, take indent of current line and increase,
            # else set indent to the same indent of the token after the indent-opener.
            scheme = isinstance(found.token(), ly.tokenize.scheme.OpenParen)
            if lasttokens:
                if isinstance(lasttokens[-1], ly.tokenize.Indent):
                    indent_pos = lasttokens[-1].pos
                elif len(lasttokens) >= 2:
                    if (scheme and lasttokens[-1] in scheme_sync_args):
                        indent_pos = lasttokens[-2].pos
                    else:
                        indent_pos, indent_add = found.token().pos, INDENT_WIDTH
                else:
                    indent_pos = lasttokens[-1].pos
            elif scheme:
                indent_pos, indent_add = found.token().pos, 1
            else:
                # just use current indent + INDENT_WIDTH
                indent_pos = token.end if isinstance(token, ly.tokenize.Space) else 0
                indent_add = INDENT_WIDTH
        elif indents + closers == 0:
            # take over indent of current line
            indent_pos = token.end if isinstance(token, ly.tokenize.Space) else 0
        else:
            prev = prev.previous()
            continue
        
        # translate indent to real columns (expanding tabs)
        return columnPosition(prev.text(), indent_pos) + indent_add
    # e.g. on first line
    return 0


def indentable(cursor):
    """Returns True if the cursor is at a dedent token and running the auto-indenter makes sense."""
    block = cursor.block()
    pos = cursor.position() - block.position()
    for token in tokeniter.tokens(block):
        if isinstance(token, ly.tokenize.Dedent):
            if token.end >= pos:
                return True
        elif not isinstance(token, ly.tokenize.Space) or token.end >= pos:
            break


def increaseIndent(cursor):
    """Increases the indent of the line the cursor is at (or the selected lines).
    
    If there is no selection or the cursor is not in the first indent space,
    just inserts a Tab (or spaces).
    
    """
    if not changeIndent(cursor, 1):
        # just insert a tab
        # TODO: see if tabs or spaces are desired
        cursor.insertText('\t')


def decreaseIndent(cursor):
    """Decreases the indent of the line the cursor is at (or the selected lines)."""
    changeIndent(cursor, -1)


def changeIndent(cursor, direction):
    """Changes the indent in the desired direction (-1 for left and +1 for right).
    
    Returns True if the indent operation was applied.
    The cursor may contain a selection.
    
    """
    blocks = list(tokeniter.selectedBlocks(cursor))
    block = blocks[0]
    pos = cursor.selectionStart() - block.position()
    token = tokeniter.tokens(block)[0] if tokeniter.tokens(block) else None
    if cursor.hasSelection() or pos == 0 or (token and isinstance(token, ly.tokenize.Space) and token.end >= pos):
        # decrease the indent
        state = tokeniter.state(block)
        current_indent = getIndent(block)
        new_indent = current_indent + direction * INDENT_WIDTH
        if state.mode() in ('lilypond', 'scheme'):
            computed_indent = computeIndent(block)
            if computed_indent is not None and cmp(computed_indent, new_indent) == direction:
                new_indent = computed_indent
        diff = new_indent - current_indent
        with tokeniter.editBlock(cursor):
            for block in blocks:
                setIndent(block, getIndent(block) + diff)
        return True


def getIndent(block):
    """Returns the indent of the given block."""
    tokens = tokeniter.tokens(block)
    if tokens and isinstance(tokens[0], ly.tokenize.Space):
        return columnPosition(tokens[0])
    return 0


def setIndent(block, indent):
    """Sets the indent of block to tabs/spaces of length indent."""
    cursor = QTextCursor(block)
    tokens = tokeniter.tokens(block)
    if tokens and isinstance(tokens[0], ly.tokenize.Space):
        cursor = tokeniter.cursor(block, tokens[0])
    cursor.insertText(makeIndent(indent))


def columnPosition(text, position=None, tabwidth = 8):
    """Converts position (or the length of the text) to real column position, expanding tabs."""
    indent, pos = 0, 0
    end = len(text) if position is None else position
    while True:
        try:
            tab = text.index('\t', pos, end)
        except ValueError:
            return indent + end - pos
        indent = (indent + tab + tabwidth) & -tabwidth
        pos = tab + 1


def makeIndent(indent, tabwidth = 8, allowTabs = ALLOW_TABS):
    """Creates a string of indent length indent, using spaces (and tabs if allowTabs)."""
    if indent <= 0:
        return ''
    elif allowTabs:
        tabs, spaces = divmod(indent, tabwidth)
        return '\t' * tabs + ' ' * spaces
    else:
        return ' ' * indent


