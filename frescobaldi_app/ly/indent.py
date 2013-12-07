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
    
    def compute_indent(self, document, block):
        """Return the indent the given block should have."""
        line = Line(document.tokens(block))
        


class Line(object):
    """Brings together all relevant information about a line (block)."""
    def __init__(self, tokens):
        """Initialize with tuple of tokens.
        
        After init, the following attributes are set:
        
        indent
        
        The indent the current line has. This is a string containing 
        whitespace (i.e. spaces and/or tabs) which can be empty. A special 
        case is False, which means the current line is not indentable, e.g. 
        it is a multiline string and should never be automatically be 
        re-indented.
        
        
        dedenters_start
        
        The number of dedent tokens that should cause the indenter to go a 
        level up.
        
        
        dedenters_end
        
        The number of dedent tokens that should cause the next line to go a 
        level up.
        
        
        indenters
        
        A list of two-item lists. The first item is the token that start a 
        new indent which is still open at the end of the line, the second 
        item (if not None) is a token after the indent token, the next line 
        could align to. This can cause the indenter not to start a new 
        indent level, but rather align stuff to the specified token's 
        position.
        
        
        """
        
        # current indent
        self.indent = ""
        if tokens:
            t = tokens[0]
            if isinstance(t, ly.lex.Space):
                self.indent = t
            elif isinstance(t, ly.lex.String) and not isinstance(t, ly.lex.StringStart):
                self.indent = False

        find_dedenters = True
        self.dedenters_start = 0
        self.dedenters_end = 0
        self.indenters = i = []
        
        def add_alignable(token):
            if i and (i[-1][1] is None or self.is_alignable_scheme_keyword(i[-1][1])):
                i[-1][1] = token
        
        for t in tokens:
            if isinstance(t, ly.lex.Indent):
                find_dedenters = False
                add_alignable(t)
                i.append([t, None])
            elif isinstance(t, ly.lex.Dedent):
                if find_dedenters and not isinstance(t, ly.lex.scheme.CloseParen):
                    self.dedenters_start += 1
                else:
                    find_dedenters = False
                    if i:
                        i.pop()
                    else:
                        self.dedenters_end += 1
            elif not isinstance(t, ly.lex.Space):
                find_dedenters = False
                add_alignable(t)
    
    def is_alignable_scheme_keyword(self, token):
        """Return True if token is an alignable Scheme word like "if", etc."""
        return isinstance(token, ly.lex.scheme.Word) and token in (

            # Scheme commands that can have one argument on the same line and 
            # then want the next arguments on the next lines at the same 
            # position.
            'if', 'and', 'or', 'set!',
            '=', '<', '<=', '>', '>=',
            'eq?', 'eqv?', 'equal?',
            'filter',
        )

