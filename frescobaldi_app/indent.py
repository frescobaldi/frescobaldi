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
Indent and auto-indent.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings
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


def indent_variables(document):
    """Return a dictionary with the indent variables for the document."""
    s = QSettings()
    s.beginGroup("indent")
    nspaces = s.value("indent_spaces", 2, int)
    tabwidth = s.value("tab_width", 8, int)
    dspaces = s.value("document_spaces", 8, int)
    return variables.update(document, {
        'indent-tabs': nspaces == 0,
        'indent-width': 2 if nspaces == 0 else nspaces,
        'tab-width': tabwidth,
        'document-tabs': dspaces == 0,
        'document-tab-width': 8 if dspaces == 0 else dspaces,
    })
    
def indenter(document):
    """Return a ly.indent.Indenter, setup for the document."""
    indent_vars = indent_variables(document)
    import ly.indent
    i = ly.indent.Indenter()
    i.indent_width = indent_vars['indent-width']
    i.indent_tabs = indent_vars['indent-tabs']
    return i
    
def auto_indent_block(block):
    """Auto-indents the given block."""
    import lydocument
    i = indenter(block.document())
    d = lydocument.LyDocument(block.document())
    current_indent = i.get_indent(d, block)
    if current_indent is False:
        return
    indent = i.compute_indent(d, block)
    d.combine_undo = True
    with d:
        d[d.position(block):d.position(block)+len(current_indent)] = indent

def compute_indent(block):
    """Returns the indent the given block should have."""
    
    # get some variables from the document
    indent_vars = indent_variables(block.document())
    
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
        
        token = None # in case of empty line
        for token in reversed(tokeniter.tokens(prev)):
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
        return column_position(prev.text(), indent_pos, indent_vars['tab-width']) + indent_add
    # e.g. on first line
    return 0


def indentable(cursor):
    """Returns True if the cursor is at a dedent token and running the auto-indenter makes sense."""
    block = cursor.block()
    pos = cursor.position() - block.position()
    for token in tokeniter.tokens(block):
        if token.end >= pos:
            return isinstance(token, ly.lex.Dedent)
        elif not isinstance(token, (ly.lex.Space, ly.lex.Dedent)):
            return


def increase_indent(cursor):
    """Increases the indent of the line the cursor is at (or the selected lines).
    
    If there is no selection or the cursor is not in the first indent space,
    just inserts a Tab (or spaces).
    
    """
    import lydocument
    c = lydocument.cursor(cursor, select_all=False)
    indenter(cursor.document()).increase_indent(c)


def decrease_indent(cursor):
    """Decreases the indent of the line the cursor is at (or the selected lines)."""
    import lydocument
    c = lydocument.cursor(cursor, select_all=False)
    indenter(cursor.document()).decrease_indent(c)


def change_indent(cursor, direction):
    """Changes the indent in the desired direction (-1 for left and +1 for right).
    
    Returns True if the indent operation was applied.
    The cursor may contain a selection.
    
    """
    # get some variables from the document
    indent_vars = indent_variables(cursor.document())
    
    blocks = list(cursortools.blocks(cursor))
    block = blocks[0]
    pos = cursor.selectionStart() - block.position()
    token = tokeniter.tokens(block)[0] if tokeniter.tokens(block) else None
    if cursor.hasSelection() or pos == 0 or (token and isinstance(token, ly.lex.Space) and token.end >= pos):
        # decrease the indent
        state = tokeniter.state(block)
        current_indent = get_indent(block)
        new_indent = current_indent + direction * indent_vars['indent-width']
        if state.mode() in ('lilypond', 'scheme'):
            computed_indent = compute_indent(block)
            if cmp(computed_indent, new_indent) == direction:
                new_indent = computed_indent
        diff = new_indent - current_indent
        with cursortools.compress_undo(cursor):
            for block in blocks:
                set_indent(block, get_indent(block) + diff)
        return True


def re_indent(cursor):
    """Re-indents the selected region or the whole document."""
    import lydocument
    c = lydocument.cursor(cursor)
    indenter(cursor.document()).indent(c)


def get_indent(block):
    """Returns the indent of the given block."""
    
    # get some variables from the document
    indent_vars = indent_variables(block.document())
    
    tokens = tokeniter.tokens(block)
    if tokens and isinstance(tokens[0], ly.lex.Space):
        return column_position(tokens[0], tabwidth = indent_vars['tab-width'])
    return 0


def set_indent(block, indent):
    """Sets the indent of block to tabs/spaces of length indent.
    
    Does not change the document if the indent does not need a change.
    Returns True if the indent was changed.
    
    """
    # get some variables from the document
    indent_vars = indent_variables(block.document())
    
    space = make_indent(indent, indent_vars['tab-width'], indent_vars['indent-tabs'])
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


def column_position(text, position=None, tabwidth = 8):
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


def make_indent(indent, tabwidth = 8, allowTabs = False):
    """Creates a string of indent length indent, using spaces (and tabs if allowTabs)."""
    if indent <= 0:
        return ''
    elif allowTabs:
        tabs, spaces = divmod(indent, tabwidth)
        return '\t' * tabs + ' ' * spaces
    else:
        return ' ' * indent


def insert_text(cursor, text):
    """Inserts text and indents it if there are newlines in it."""
    if '\n' not in text:
        cursor.insertText(text)
        return
    line = cursor.document().findBlock(cursor.selectionStart()).blockNumber()
    with cursortools.compress_undo(cursor):
        cursor.insertText(text)
        block = cursor.document().findBlockByNumber(line)
        last = cursor.block()
        tokeniter.update(block) # tokenize inserted lines
        while last != block:
            block = block.next()
            if set_indent(block, compute_indent(block)):
                tokeniter.update(block)


