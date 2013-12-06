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



