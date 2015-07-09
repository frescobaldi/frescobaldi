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
Generate meaningful tooltips for cursor positions.
"""

from __future__ import unicode_literals

import tokeniter
import ly.lex.lilypond


def text(cursor):
    filename = cursor.document().documentName()
    line = cursor.blockNumber() + 1
    column = cursor.position() - cursor.block().position()
    text = "{0} ({1}:{2})".format(filename, line, column)
    definition = get_definition(cursor)
    if definition:
        text += '\n' + definition
    time_pos = time_position(cursor)
    if time_pos:
        text += '\n' + _("Position: {pos}").format(pos=time_pos)
    return text

def get_definition(cursor):
    block = cursor.block()
    while block.isValid():
        state = tokeniter.state(block)
        if isinstance(state.parser(), ly.lex.lilypond.ParseGlobal):
            for t in tokeniter.tokens(block)[:2]:
                if type(t) is ly.lex.lilypond.Name:
                    return t[:]
                elif isinstance(t, ly.lex.lilypond.Keyword) and t == '\\score':
                    return '\\score'
        block = block.previous()

def time_position(cursor):
    import documentinfo
    pos = documentinfo.music(cursor.document()).time_position(cursor.position())
    if pos is not None:
        import ly.duration
        return ly.duration.format_fraction(pos)


