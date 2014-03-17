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

from __future__ import unicode_literals

import ly.lex.lilypond
import ly.lex.scheme


class Indenter(object):
    
    # variables
    indent_tabs = False     # use tabs for indent
    indent_width = 2        # amount of spaces if indent_tabs == False
    
    def __init__(self):
        pass
    
    def indent(self, cursor, indent_blank_lines=False):
        """Indent all lines in the cursor's range.
        
        If indent_blank_lines is True, the indent of blank lines is made 
        larger if necessary. If False (the default), the indent of blank 
        lines if not changed if it is shorter than it should be.
        
        """
        indents = ['']
        start_block, end_block = cursor.start_block(), cursor.end_block()
        in_range = False
        pline = None
        prev_indent = ''
        with cursor.document as d:
            for b in cursor.document:
                if b == start_block:
                    in_range = True
                
                line = Line(d, b)
                
                # handle indents of prev line
                if pline:
                    if pline.indent != False:
                        prev_indent = pline.indent
                    if pline.indenters:
                        current_indent = indents[-1]
                        for align, indent in pline.indenters:
                            new_indent = current_indent
                            if align:
                                new_indent += ' ' * (align - len(prev_indent))
                            if indent:
                                new_indent += '\t' if self.indent_tabs else ' ' * self.indent_width
                            indents.append(new_indent)
                del indents[max(1, len(indents) - line.dedenters_start):]
                
                # if we may not change the indent just remember the current
                if line.indent is not False:
                    if not in_range:
                        indents[-1] = line.indent
                    elif not indent_blank_lines and line.isblank and indents[-1].startswith(line.indent):
                        pass # don't make shorter indents longer on blank lines
                    elif line.indent != indents[-1]:
                        d[d.position(b):d.position(b)+len(line.indent)] = indents[-1]
                del indents[max(1, len(indents) - line.dedenters_end):]
                
                if b == end_block:
                    break
                
                pline = line
    
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
    
    def get_indent(self, document, block):
        """Return the indent the block currently has.
        
        Returns False if the block is not indentable, e.g. when it is part of
        a multiline string.
        
        """
        return Line(document, block).indent
    
    def compute_indent(self, document, block):
        """Return the indent the specified block should have.
        
        Returns False if the block is not indentable, e.g. when it is part of
        a multiline string.
        
        This method is used to determine the indent of one line, and just 
        looks to previous lines, copying the indent of the line where the 
        current indent depth starts, and/or adding a level of indent or 
        alignment space.
        
        Use this method only for one line or the first of a group you're 
        indenting.
        
        """
        line = Line(document, block)
        if line.indent is False:
            return False
        depth = line.dedenters_start
        blocks = document.blocks_backward(document.previous_block(block))
        align, indent = None, False
        for b in blocks:
            line = Line(document, b)
            indents = len(line.indenters)
            if 0 <= depth < indents:
                # we found the indent token
                index = indents - depth - 1
                align, indent = line.indenters[index]
                break
            depth -= indents
            depth += line.dedenters_end
            if depth == 0:
                # same indent as this line
                break
            depth += line.dedenters_start
        else:
            return ""
        
        # here we arrive after 'break'
        i = line.indent
        if i == False:
            for b in blocks:
                i = Line(document, b).indent
                if i != False:
                    break
            else:
                i = ""
        if align:
            i += ' ' * (align - len(i))
        if indent:
            i += '\t' if self.indent_tabs else ' ' * self.indent_width
        return i


class Line(object):
    """Brings together all relevant information about a line (block)."""
    def __init__(self, document, block):
        """Initialize with a block (line) of the document.
        
        After init, the following attributes are set:
        
        indent
        
        The indent the current line has. This is a string containing 
        whitespace (i.e. spaces and/or tabs) which can be empty. A special 
        case is False, which means the current line is not indentable, e.g. 
        it is a multiline string and should never be automatically be 
        re-indented.
        
        
        isblank
        
        True if the line is empty or white-space only. It is False when the 
        indent attribute is also False (e.g. when the line is part of a 
        multiline string).
        
        
        dedenters_start
        
        The number of dedent tokens that should cause the indenter to go a 
        level up.
        
        
        dedenters_end
        
        The number of dedent tokens that should cause the next line to go a 
        level up.
        
        
        indenters
        
        A list of tuples (align, indent). Each item corresponds with an 
        indent that starts on the line. The align value (integer) determines 
        the position the next line should be padded to with spaces, 0 or 
        None means no alignment. The indent value (bool) specifies if there 
        should a new indent level be added (a tab or some amount of spaces).
        
        """
        state = document.state(block)
        tokens = document.tokens(block)
        
        # are we in a multi-line string?
        if isinstance(state.parser(), (
            ly.lex.lilypond.ParseString,
            ly.lex.scheme.ParseString,
            )):
            self.indent = False
            self.isblank = False
        # or a multi-line comment?
        elif isinstance(state.parser(), (
            ly.lex.lilypond.ParseBlockComment,
            ly.lex.scheme.ParseBlockComment,
            )):
            # do allow indent the last line of a block comment if it only
            # contains space
            if tokens and isinstance(tokens[0], ly.lex.BlockCommentEnd):
                self.indent = ""
            elif (len(tokens) > 1
                  and isinstance(tokens[0], ly.lex.BlockComment)
                  and isinstance(tokens[1], ly.lex.BlockCommentEnd)
                  and tokens[0].isspace()):
                self.indent = tokens[0]
            else:
                self.indent = False
            self.isblank = False
        elif tokens and isinstance(tokens[0], ly.lex.Space):
            self.indent = tokens[0]
            self.isblank = len(tokens) == 1
        else:
            self.indent = ""
            self.isblank = not tokens

        find_dedenters = True
        self.dedenters_start = 0
        self.dedenters_end = 0
        
        # quickly iter over the tokens, collecting the indent tokens and 
        # possible stuff to align to after the indent tokens
        indenters = []
        for t in tokens:
            if isinstance(t, ly.lex.Indent):
                find_dedenters = False
                if indenters:
                    indenters[-1].append(t)
                indenters.append([t])
            elif isinstance(t, ly.lex.Dedent):
                if find_dedenters and not isinstance(t, ly.lex.scheme.CloseParen):
                    self.dedenters_start += 1
                else:
                    find_dedenters = False
                    if indenters:
                        indenters.pop()
                    else:
                        self.dedenters_end += 1
            elif not isinstance(t, ly.lex.Space):
                find_dedenters = False
                if indenters:
                    indenters[-1].append(t)
        
        # now analyse the indent tokens that are not closed on the same line
        # and determine how the next line should be indented
        self.indenters = []
        for indent in indenters:
            token, rest = indent[0], indent[1:]
            if isinstance(token, ly.lex.scheme.OpenParen):
                if len(rest) > 1 and self.is_alignable_scheme_keyword(rest[0]):
                    align, indent = rest[1].pos, False
                elif len(rest) == 1 and not isinstance(rest[0], ly.lex.Comment):
                    align, indent = rest[0].pos, False
                else:
                    align, indent = token.pos, True
            elif rest and not isinstance(rest[0], ly.lex.Comment):
                align, indent = rest[0].pos, False
            else:
                align, indent = None, True
            self.indenters.append((align, indent))
    
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

