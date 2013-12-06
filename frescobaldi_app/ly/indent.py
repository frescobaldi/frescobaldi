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

import ly.lex.lilypond
import ly.lex.scheme


class Indenter(object):
    
    # variables
    indent_tabs = False
    indent_width = 2
    
    def __init__(self):
        pass
    
    def indent(self, cursor):
        """Indent all lines in the cursor's range."""
        
    def increase_indent(self, cursor):
        """Manually add indent to all lines of cursor."""
        indent = '\t' if self.indent_tabs else ' ' * self.indent_width
        with cursor.document as d:
            for block in cursor.blocks():
                ins = d.position(block)
                tokens = d.tokens(block)
                if tokens and isinstance(tokens[0], ly.lex.Space):
                    tab_pos = tokens[0].rfind('\t')
                    if tab_pos != -1:
                        ins += tokens[0].pos + tab_pos + 1
                    else:
                        ins += tokens[0].end
                d[ins:ins] = indent
    
    def decrease_indent(self, cursor):
        """Manually remove one level of indent from all lines of cursor."""
        with cursor.document as d:
            for block in cursor.blocks():
                tokens = d.tokens(block)
                if tokens:
                    token = tokens[0]
                    if isinstance(token, ly.lex.Space):
                        space = token
                    else:
                        space = token[0:-len(token.lstrip())]
                    pos = d.position(block)
                    end = pos + len(space)
                    if '\t' in space and space.endswith(' '):
                        # strip alignment
                        del d[pos + space.rfind('\t') + 1 : end]
                    elif space.endswith('\t'):
                        # just strip one tab
                        del d[end - 1]
                    elif space.endswith(' ' * self.indent_width):
                        del d[end - self.indent_width: end]
                    else:
                        del d[pos:end]
        






# scheme commands that can have one argument on the same line and then want the next arguments
# on the next lines at the same position.
scheme_sync_args = (
    'if', 'and', 'or', 'set!',
    '=', '<', '<=', '>', '>=',
    'eq?', 'eqv?', 'equal?',
    'filter',
)


def auto_indent_block(block):
    """Auto-indents the given block."""
    set_indent(block, compute_indent(block))


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
        elif not isinstance(token, ly.lex.Space):
            return


def increase_indent(cursor):
    """Increases the indent of the line the cursor is at (or the selected lines).
    
    If there is no selection or the cursor is not in the first indent space,
    just inserts a Tab (or spaces).
    
    """
    if not change_indent(cursor, 1):
        # just insert a tab
        indent_vars = indent_variables(cursor.document())
        if indent_vars['document-tabs']:
            cursor.insertText('\t')
        else:
            block = cursor.block()
            tabwidth = indent_vars['tab-width']
            pos = column_position(block.text(), cursor.position() - block.position(), tabwidth)
            spaces = tabwidth - pos % tabwidth
            cursor.insertText(' ' * spaces)


def decrease_indent(cursor):
    """Decreases the indent of the line the cursor is at (or the selected lines)."""
    change_indent(cursor, -1)


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
    if cursor.hasSelection():
        blocks = cursortools.blocks(cursor)
    else:
        blocks = cursortools.all_blocks(cursor.document())
    with cursortools.compress_undo(cursor):
        for block in blocks:
            tokeniter.update(block)
            if tokeniter.state(block).mode() in ('lilypond', 'scheme'):
                indent = compute_indent(block)
            else:
                indent = get_indent(block)
            if set_indent(block, indent):
                tokeniter.update(block) # force token update if changed


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


def indent_variables(document):
    """Returns a dictionary with some variables regarding document indenting."""
    return variables.update(document, {
        'indent-width': 2,
        'tab-width': 8,
        'indent-tabs': False,
        'document-tabs': True,
    })


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


