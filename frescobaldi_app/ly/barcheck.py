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
Add, check or remove bar checks in selected music.
"""

from __future__ import unicode_literals

import itertools

import ly.document
import ly.lex.lilypond


def remove(cursor):
    """Remove bar checks from the selected music."""
    s = ly.document.Source(cursor, tokens_with_position=True)
    prv, cur = None, None
    with cursor.document as d:
        for nxt in itertools.chain(s, (None,)):
            if isinstance(cur, ly.lex.lilypond.PipeSymbol):
                if isinstance(prv, ly.lex.Space):
                    # pipesymbol and adjacent space may be deleted
                    if nxt == '\n':
                        del d[prv.pos:cur.end]
                    elif isinstance(nxt, ly.lex.Space):
                        del d[cur.pos:nxt.end]
                    else:
                        del d[cur.pos:cur.end]
                elif isinstance(nxt, ly.lex.Space):
                    # delete if followed by a space 
                    del d[cur.pos:cur.end]
                else:
                    # replace "|" with a space
                    d[cur.pos:cur.end] = " "
            prv, cur = cur, nxt


