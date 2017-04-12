# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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


from PyQt5.QtCore import QSettings

import ly.lex
import ly.indent
import cursortools
import tokeniter
import variables
import lydocument


def indent_variables(document=None):
    """Return a dictionary with indentation preferences.

    If a document (a Frescobaldi/QTextDocument) is specified, the document
    variables are also read.

    For the variables and their default variables, see userguide/docvars.md.

    """
    s = QSettings()
    s.beginGroup("indent")
    nspaces = s.value("indent_spaces", 2, int)
    tabwidth = s.value("tab_width", 8, int)
    dspaces = s.value("document_spaces", 8, int)
    prefs = {
        'indent-tabs': nspaces == 0,
        'indent-width': 2 if nspaces == 0 else nspaces,
        'tab-width': tabwidth,
        'document-tabs': dspaces == 0,
        'document-tab-width': 8 if dspaces == 0 else dspaces,
    }
    return variables.update(document, prefs) if document else prefs

def indenter(document=None):
    """Return a ly.indent.Indenter, setup for the document."""
    indent_vars = indent_variables(document)
    i = ly.indent.Indenter()
    i.indent_width = indent_vars['indent-width']
    i.indent_tabs = indent_vars['indent-tabs']
    return i

def auto_indent_block(block):
    """Auto-indents the given block."""
    i = indenter(block.document())
    d = lydocument.Document(block.document())
    current_indent = i.get_indent(d, block)
    if current_indent is False:
        return
    indent = i.compute_indent(d, block)
    d.combine_undo = True
    with d:
        d[d.position(block):d.position(block)+len(current_indent)] = indent

def indentable(cursor):
    """Returns True if the cursor is at a dedent token and running the auto-indenter makes sense."""
    block = cursor.block()
    pos = cursor.position() - block.position()
    for token in tokeniter.tokens(block):
        if token.end >= pos:
            return isinstance(token, (ly.lex.Dedent, ly.lex.BlockCommentEnd))
        elif not isinstance(token, (ly.lex.Space, ly.lex.Dedent)):
            return

def increase_indent(cursor):
    """Increases the indent of the line the cursor is at (or the selected lines).

    If there is no selection or the cursor is not in the first indent space,
    just inserts a Tab (or spaces).

    """
    c = lydocument.cursor(cursor)
    indenter(cursor.document()).increase_indent(c)

def decrease_indent(cursor):
    """Decreases the indent of the line the cursor is at (or the selected lines)."""
    c = lydocument.cursor(cursor)
    indenter(cursor.document()).decrease_indent(c)

def re_indent(cursor, indent_blank_lines=False):
    """Re-indents the selected region or the whole document.

    If indent_blank_lines is True, the indent of blank lines is made larger
    if necessary. If False (the default), the indent of blank lines if not
    changed if it is shorter than it should be.

    """
    c = lydocument.cursor(cursor, select_all=True)
    indenter(cursor.document()).indent(c, indent_blank_lines)

