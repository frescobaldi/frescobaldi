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
        # count the dedent tokens at the beginning of the block
        indents = 0
        for token in document.tokens(block):
            # dont dedent scheme dedent tokens at beginning of lines (unusual)
            if isinstance(token, ly.lex.Dedent) and not isinstance(token, ly.lex.scheme.CloseParen):
                indents -= 1
            elif not isinstance(token, ly.lex.Space):
                break
        
        # look backwards for the token that starts this indent
        prev = document.previous_block(block)
        while document.isvalid(prev):
            
            tokens = document.tokens(prev)
            state = document.state(prev)
            
            # do not look at the indent of certain blocks
            if not tokens or isinstance(state.parser(), (
                    ly.lex.lilypond.ParseString,
                    ly.lex.scheme.ParseString,
                )):
                prev = document.previous_block(prev)
            
            closers = 0
            found = False
            lasttokens = []
            
            token = None # in case of empty line
            
            # find the token that starts this indent level, also watching
            # other tokens that might appear after it
            for token in reversed(tokens):
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
            
            if isinstance(token, ly.lex.Space):
                old_indent = token
            else:
                old_indent = ""
            
            indent_add = False
            align_pos = 0
            
            if found:
                # the token that started the current indent has been found.
                # if there are no tokens after the indent-opener, take indent 
                # of current line and increase, else dont increase the indent
                # but align to the token after the indent-opener.
                if isinstance(found, ly.lex.scheme.OpenParen):
                    # scheme
                    align_pos = found.pos
                    indent_add = True
                    if lasttokens:
                        if len(lasttokens) == 1 or isinstance(lasttokens[-1], ly.lex.Indent):
                            align_pos = lasttokens[-1].pos
                            indent_add = False
                        elif lasttokens[-1] in scheme_sync_args:
                            align_pos = lasttokens[-2].pos
                            indent_add = False
                else:
                    # no scheme (lilypond)
                    if lasttokens:
                        align_pos = lasttokens[-1].pos
                    else:
                        # just use current indent + INDENT_WIDTH
                        align_pos = token.end if isinstance(token, ly.lex.Space) else 0
                        indent_add = True
            elif indents + closers != 0:
                prev = document.previous_block(prev)
                continue
            
            # take over indent of current line
            break
            
            # translate indent to real columns (expanding tabs)
            
            return column_position(prev.text(), indent_pos, indent_vars['tab-width']) + indent_add
        # e.g. on first line
        return 0
            



