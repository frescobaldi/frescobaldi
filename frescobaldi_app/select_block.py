# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013- 2013 by Wilbert Berendsen
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
Select Block.
"""

from __future__ import unicode_literals


import ly.lex
import lydocument


def find(i):
    """Yield (token, is_indent, nest) for every occurring indent/dedent token in i."""
    nest = 0
    for token in i:
        if isinstance(token, ly.lex.Indent):
            nest += 1
            yield token, True, nest
        elif isinstance(token, ly.lex.Dedent):
            nest -= 1
            yield token, False, nest


def select_block(cursor):
    """Try to select a meaningful block.
    
    Always extends the selection.
    Returns True if the cursor's selection has changed.
    
    """
    c = lydocument.cursor(cursor)
    end = c.end if c.end is not None else c.document.size()
    tokens = lydocument.Runner.at(c, after_token=True)
    # search backwards to the first indenting token
    for token, isindent, nest in find(tokens.backward()):
        if isindent and nest == 1:
            pos1 = tokens.position()
            startpoint = tokens.copy()
            # found, now look forward
            for token, isindent, nest in find(tokens.forward()):
                if not isindent and nest < 0 and tokens.position() + len(token) >= end:
                    # we found the endpoint
                    pos2 = tokens.position() + len(token)
                    if nest < -1:
                        threshold = 1 - nest
                        for token, isindent, nest in find(startpoint.backward()):
                            if isindent and nest == threshold:
                                pos1 = tokens.position()
                                break
                    cursor.setPosition(pos2)
                    cursor.setPosition(pos1, cursor.KeepAnchor)
                    return True
            return

