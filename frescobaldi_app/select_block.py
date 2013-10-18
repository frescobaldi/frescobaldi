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


import tokeniter
import ly.lex


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
    doc = cursor.document()
    start, end = cursor.selectionStart(), cursor.selectionEnd()
    
    # search backwards to the first indent token
    first_block = doc.findBlock(start)
    column = start - first_block.position()
    tokens = tokeniter.Runner(first_block)
    
    c1, c2 = None, None
    # go to the cursor position 
    for token in tokens.forward_line():
        if token.pos <= column <= token.end:
            # we are at the cursor position
            if not isinstance(token, ly.lex.Indent):
                # search backwards to the first indenting token
                for token, isindent, nest in find(tokens.backward()):
                    if isindent and nest == 1:
                        break
                else:
                    return
            c1 = tokens.cursor()
            startpoint = tokens.copy()
            # now look forward
            for token, isindent, nest in find(tokens.forward()):
                if not isindent and nest < 0 and  tokens.block.position() + token.end >= end:
                    # we found the endpoint
                    c2 = tokens.cursor()
                    if nest < -1:
                        threshold = 1 - nest
                        for token, isindent, nest in find(startpoint.backward()):
                            if isindent and nest == threshold:
                                c1 = tokens.cursor()
                                break
                    cursor.setPosition(c2.selectionEnd())
                    cursor.setPosition(c1.selectionStart(), cursor.KeepAnchor)
                    return True

