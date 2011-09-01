# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 by Wilbert Berendsen
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
Analyze text to determine suitable completions.
"""

from __future__ import unicode_literals

import re

import ly.lex.lilypond
import ly.words
import tokeniter

from . import completiondata


def completions(cursor):
    """Analyzes text at cursor and returns a tuple (position, model) or None.
    
    The position is an integer specifying the column in the line where the last
    text starts that should be completed.
    
    The model list the possible completions.
    
    If None is returned. there are no suitable completions.
    
    This function does its best to return extremely meaningful completions
    for the context the cursor is in.
    
    """
    block = cursor.block()
    column = cursor.position() - block.position()
    text = block.text()[:column]
    
    # make a list of tokens exactly ending at the cursor position
    # and let state follow
    state = tokeniter.state(block)
    tokens = []
    for t in tokeniter.tokens(cursor.block()):
        if t.end > column:
            # cut off the last token and run the parser on it
            tokens.extend(state.tokens(text, t.pos))
            break
        tokens.append(t)
        state.follow(t)
        if t.end == column:
            break
    
    last = tokens[-1] if tokens else ''
    
    # DEBUG
    print '================================'
    for t in tokens:
        print '{0} "{1}"'.format(t.__class__.__name__, t)
    
    # in markup mode?
    if isinstance(state.parser(), ly.lex.lilypond.MarkupParser):
        if last.startswith('\\') and last[1:] not in ly.words.markupcommands:
            column = last.pos
        return column, completiondata.lilypond_markup_commands
    
    # TEMP!!! only complete backslashed commands
    m = re.search(r'\\[a-z]?[A-Za-z]*$', text)
    if m:
        return m.start(), completiondata.lilypond_commands


