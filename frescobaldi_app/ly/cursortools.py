# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
Routines manipulating ly.document.Cursor instances.

"""

from __future__ import unicode_literals


import ly.lex
import ly.document


def find_indent(iterable):
    """Yield (token, is_indent, nest) for every occurring indent/dedent token.
    
    The tokens are yielded from the specified iterable.
    
    """
    nest = 0
    for token in iterable:
        if isinstance(token, ly.lex.Indent):
            nest += 1
            yield token, True, nest
        elif isinstance(token, ly.lex.Dedent):
            nest -= 1
            yield token, False, nest


def select_block(cursor):
    """Try to select a meaningful block.
    
    Searches backwards for an indenting token, then selects up to the 
    corresponding dedenting token. If needed searches an extra level back to 
    always extend the selection. Returns True if the cursor's selection has 
    changed.
    
    """
    end = cursor.end if cursor.end is not None else cursor.document.size()
    tokens = ly.document.Runner.at(cursor, after_token=True)
    # search backwards to the first indenting token
    for token, isindent, nest in find_indent(tokens.backward()):
        if isindent and nest == 1:
            pos1 = tokens.position()
            startpoint = tokens.copy()
            # found, now look forward
            for token, isindent, nest in find_indent(tokens.forward()):
                if not isindent and nest < 0 and tokens.position() + len(token) >= end:
                    # we found the endpoint
                    pos2 = tokens.position() + len(token)
                    if nest < -1:
                        threshold = 1 - nest
                        for token, isindent, nest in find_indent(startpoint.backward()):
                            if isindent and nest == threshold:
                                pos1 = tokens.position()
                                break
                    cursor.start, cursor.end = pos1, pos2
                    return True
            return

