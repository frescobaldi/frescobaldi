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
Indent and auto-indent.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QTextCursor

import ly.lex
import ly.lex.scheme
import cursortools
import tokeniter
import variables


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
    
    # get some variables from the document
    indent_vars = indentVariables(block.document())
    
    # count the dedent tokens at the beginning of the block
    indents = 0
    for token in tokeniter.tokens(block):
        # dont dedent scheme dedent tokens at beginning of lines (unusual)
        if isinstance(token, ly.lex.Dedent) and not isinstance(token, ly.lex.scheme.CloseParen):
            indents -= 1
        elif not isinstance(token, ly.lex.Space):
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
            if isinstance(token, ly.lex.Dedent):
                indents -= 1
                if isinstance(token, ly.lex.scheme.CloseParen):
                    closers = 0 # scheme close parens are not moved
                else:
                    closers += 1
            elif isinstance(token, ly.lex.Indent):
                indents += 1
                closers = 0
                if not found:
                    if indents == 1:
                        found = token
                    else:
                        lasttokens.append(token)
            elif not isinstance(token, ly.lex.Space):
                closers = 0
                if not found:
                    lasttokens.append(token)
        
        if found:
            # the token that started the current indent has been found
            # if there are no tokens after the indent-opener, take indent of current line and increase,
            # else set indent to the same indent of the token after the indent-opener.
            if isinstance(found, ly.lex.scheme.OpenParen):
                # scheme
                if lasttokens:
                    if len(lasttokens) == 1 or isinstance(lasttokens[-1], ly.lex.Indent):
                        indent_pos = lasttokens[-1].pos
                    elif lasttokens[-1] in scheme_sync_args:
                        indent_pos = lasttokens[-2].pos
                    else:
                        indent_pos = found.pos
                        indent_add = indent_vars['indent-width']
                else:
                    indent_pos = found.pos
                    indent_add = 1
            else:
                # no scheme (lilypond)
                if lasttokens:
                    indent_pos = lasttokens[-1].pos
                else:
                    # just use current indent + INDENT_WIDTH
                    indent_pos = token.end if isinstance(token, ly.lex.Space) else 0
                    indent_add = indent_vars['indent-width']
        elif indents + closers == 0:
            # take over indent of current line
            indent_pos = token.end if isinstance(token, ly.lex.Space) else 0
        else:
            prev = prev.previous()
            continue
        
        # translate indent to real columns (expanding tabs)
        return columnPosition(prev.text(), indent_pos, indent_vars['tab-width']) + indent_add
    # e.g. on first line
    return 0


def indentable(cursor):
    """Returns True if the cursor is at a dedent token and running the auto-indenter makes sense."""
    block = cursor.block()
    pos = cursor.position() - block.position()
    for token in tokeniter.tokens(block):
        if isinstance(token, ly.lex.Dedent):
            if token.end >= pos:
                return True
        elif not isinstance(token, ly.lex.Space) or token.end >= pos:
            break


def increaseIndent(cursor):
    """Increases the indent of the line the cursor is at (or the selected lines).
    
    If there is no selection or the cursor is not in the first indent space,
    just inserts a Tab (or spaces).
    
    """
    if not changeIndent(cursor, 1):
        # just insert a tab
        indent_vars = indentVariables(cursor.document())
        if indent_vars['document-tabs']:
            cursor.insertText('\t')
        else:
            block = cursor.block()
            tabwidth = indent_vars['tab-width']
            pos = columnPosition(block.text(), cursor.position() - block.position(), tabwidth)
            spaces = tabwidth - pos % tabwidth
            cursor.insertText(' ' * spaces)


def decreaseIndent(cursor):
    """Decreases the indent of the line the cursor is at (or the selected lines)."""
    changeIndent(cursor, -1)


def changeIndent(cursor, direction):
    """Changes the indent in the desired direction (-1 for left and +1 for right).
    
    Returns True if the indent operation was applied.
    The cursor may contain a selection.
    
    """
    # get some variables from the document
    indent_vars = indentVariables(cursor.document())
    
    blocks = list(cursortools.selectedBlocks(cursor))
    block = blocks[0]
    pos = cursor.selectionStart() - block.position()
    token = tokeniter.tokens(block)[0] if tokeniter.tokens(block) else None
    if cursor.hasSelection() or pos == 0 or (token and isinstance(token, ly.lex.Space) and token.end >= pos):
        # decrease the indent
        state = tokeniter.state(block)
        current_indent = getIndent(block)
        new_indent = current_indent + direction * indent_vars['indent-width']
        if state.mode() in ('lilypond', 'scheme'):
            computed_indent = computeIndent(block)
            if cmp(computed_indent, new_indent) == direction:
                new_indent = computed_indent
        diff = new_indent - current_indent
        with cursortools.editBlock(cursor):
            for block in blocks:
                setIndent(block, getIndent(block) + diff)
        return True


def reIndent(cursor):
    """Re-indents the selected region or the whole document."""
    if cursor.hasSelection():
        blocks = cursortools.selectedBlocks(cursor)
    else:
        blocks = cursortools.allBlocks(cursor.document())
    with cursortools.editBlock(cursor):
        for block in blocks:
            tokeniter.update(block)
            if tokeniter.state(block).mode() in ('lilypond', 'scheme'):
                indent = computeIndent(block)
            else:
                indent = getIndent(block)
            if setIndent(block, indent):
                tokeniter.update(block) # force token update if changed


def getIndent(block):
    """Returns the indent of the given block."""
    
    # get some variables from the document
    indent_vars = indentVariables(block.document())
    
    tokens = tokeniter.tokens(block)
    if tokens and isinstance(tokens[0], ly.lex.Space):
        return columnPosition(tokens[0], tabwidth = indent_vars['tab-width'])
    return 0


def setIndent(block, indent):
    """Sets the indent of block to tabs/spaces of length indent.
    
    Does not change the document if the indent does not need a change.
    Returns True if the indent was changed.
    
    """
    # get some variables from the document
    indent_vars = indentVariables(block.document())
    
    space = makeIndent(indent, indent_vars['tab-width'], indent_vars['indent-tabs'])
    tokens = tokeniter.tokens(block)
    if tokens and isinstance(tokens[0], ly.lex.Space):
        changed = tokens[0] != space
        cursor = tokeniter.cursor(block, tokens[0])
    else:
        changed = indent != 0
        cursor = QTextCursor(block)
    if changed:
        cursor.insertText(space)
    return changed


def indentVariables(document):
    """Returns a dictionary with some variables regarding document indenting."""
    return variables.update(document, {
        'indent-width': 2,
        'tab-width': 8,
        'indent-tabs': False,
        'document-tabs': True,
    })


def columnPosition(text, position=None, tabwidth = 8):
    """Converts position (or the length of the text) to real column position, expanding tabs."""
    column, pos = 0, 0
    end = len(text) if position is None else position
    while True:
        try:
            tab = text.index('\t', pos, end)
        except ValueError:
            return column + end - pos
        column = (column + tab - pos + tabwidth) & -tabwidth
        pos = tab + 1


def makeIndent(indent, tabwidth = 8, allowTabs = False):
    """Creates a string of indent length indent, using spaces (and tabs if allowTabs)."""
    if indent <= 0:
        return ''
    elif allowTabs:
        tabs, spaces = divmod(indent, tabwidth)
        return '\t' * tabs + ' ' * spaces
    else:
        return ' ' * indent


