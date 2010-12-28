# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Indent and auto-indent.
"""


import ly.tokenize
import tokeniter


def autoIndentBlock(block):
    """Auto-indents the given block."""
    
    if block.blockNumber() == 0:
        return
        
    # count the dedent tokens at the beginning of the current block
    indents = 0
    tokens = tokeniter.TokenIterator(block)
    for token in tokens.forward(False):
        if isinstance(token, ly.tokenize.Dedent):
            indents -= 1
        elif not isinstance(token, ly.tokenize.Space):
            break

    # find preceding non-empty line
    prev = block.previous()
    while prev.isValid():
        if prev.text():
            break
    else:
        return
    
    # look for both indent and dedent tokens in that line
    pos = {}
    tokens = tokeniter.TokenIterator(prev, atEnd=True)
    for token in tokens.backward(False):
        if isinstance(token, ly.tokenize.Dedent):
            indents -= 1
        elif isinstance(token, ly.tokenize.Indent):
            indents += 1
            pos[indents] = token.pos
    
    if indents == 0:
        pass # take over indent of previous line
    
    