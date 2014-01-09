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
Formatting tools to improve the readability of a ly.document.Document without
changing the semantic meaning of the LilyPond source.

Basically the tools only change whitespace to make the source-code more 
readable.

See also ly.indent.

"""

from __future__ import unicode_literals

import ly.indent
import ly.lex


def break_indenters(cursor):
    """Add newlines around indent and dedent tokens where needed.
    
    If there is stuff after a { or << (that's not closed on the same line) 
    it is put on a new line, and if there if stuff before a } or >>, the } 
    or >> is put on a new line.
    
    It is necessary to run the indenter again over the same part of the 
    document, as it will look garbled with the added newlines.
    
    """
    with cursor.document as d:
        for b in cursor.blocks():
            denters = []
            tokens = d.tokens(b)
            nonspace_index = -1
            for i, t in enumerate(tokens):
                if isinstance(t, ly.lex.Indent) and t in ('{', '<<'):
                    denters.append(i)
                elif isinstance(t, ly.lex.Dedent) and t in ('}', '>>'):
                    if denters:
                        denters.pop()
                    elif nonspace_index != -1:
                        # add newline before t
                        pos = d.position(b) + t.pos
                        d[pos:pos] = '\n'
                if not isinstance(t, ly.lex.Space):
                    nonspace_index = i
            for i in denters:
                if i < nonspace_index:
                    # add newline after tokens[i]
                    pos = d.position(b) + tokens[i].end
                    d[pos:pos] = '\n'


def move_long_comments(cursor):
    """Move line comments with more than 2 comment characters to column 0."""
    with cursor.document as d:
        for b in cursor.blocks():
            tokens = d.tokens(b)
            if (len(tokens) == 2
                and isinstance(tokens[0], ly.lex.Space)
                and isinstance(tokens[1], (
                    ly.lex.lilypond.LineComment,
                    ly.lex.scheme.LineComment))
                and tokens[1][:3] in ('%%%', ';;;')):
                del d[d.position(b):d.position(b) + tokens[1].pos]


def remove_trailing_whitespace(cursor):
    """Removes whitespace from all lines in the cursor's range."""
    with cursor.document as d:
        for b in cursor.blocks():
            tokens = d.tokens(b)
            if tokens:
                t = tokens[-1]
                end = d.position(b) + t.end
                if isinstance(t, ly.lex.Space):
                    del d[end-len(t):end]
                elif not isinstance(t, ly.lex.String):
                    offset = len(t) - len(t.rstrip())
                    if offset:
                        del d[end-offset:end]


def reformat(cursor, indenter):
    """A do-it-all function improving the LilyPond source formatting."""
    break_indenters(cursor)
    indenter.indent(cursor)
    move_long_comments(cursor)
    remove_trailing_whitespace(cursor)



