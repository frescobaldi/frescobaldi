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
Implementation of the tools to edit durations of selected music.
"""

from __future__ import unicode_literals

import cursortools
import tokeniter
import ly.lex.lilypond
import music


durations = ['\\maxima', '\\longa', '\\breve',
    '1', '2', '4', '8', '16', '32', '64', '128', '256', '512', '1024', '2048']


def rhythm_double(cursor):
    with cursortools.Editor() as e:
        for b, d in duration_items(cursor, ly.lex.lilypond.Length):
            for t in d:
                try:
                    i = durations.index(t)
                except ValueError:
                    continue
                if i > 0:
                    e.insertText(tokeniter.cursor(b, t), durations[i - 1])

def rhythm_halve(cursor):
    with cursortools.Editor() as e:
        for b, d in duration_items(cursor, ly.lex.lilypond.Length):
            for t in d:
                try:
                    i = durations.index(t)
                except ValueError:
                    continue
                if i < len(durations) - 1:
                    e.insertText(tokeniter.cursor(b, t), durations[i + 1])
    
def rhythm_dot(cursor):
    with cursortools.Editor() as e:
        for b, d in duration_items(cursor, ly.lex.lilypond.Length):
            for t in d:
                e.insertText(tokeniter.cursor(b, t, start=len(t)), ".")

def rhythm_undot(cursor):
    with cursortools.Editor() as e:
        for b, d in duration_items(cursor, ly.lex.lilypond.Dot):
            if d:
                e.removeSelectedText(tokeniter.cursor(b, d[0]))

def rhythm_remove_scaling(cursor):
    with cursortools.editBlock(cursor):
        for c in cursors(cursor, ly.lex.lilypond.Scaling):
            c.removeSelectedText()

def rhythm_remove(cursor):
    with cursortools.editBlock(cursor):
        for c in cursors(cursor, ly.lex.lilypond.Duration):
            c.removeSelectedText()

def rhythm_implicit(cursor):
    pass

def rhythm_implicit_per_line(cursor):
    pass

def rhythm_explicit(cursor):
    pass

def rhythm_apply(cursor, mainwindow):
    pass

def rhythm_copy(cursor):
    pass

def rhythm_paste(cursor):
    pass


def duration_items(cursor, *classes):
    source = tokeniter.Source.selection(cursor, True)
    for m in music.music_items(source):
        yield source.block, [token for token in m if isinstance(token, classes)]


def cursors(cursor, *classes):
    return [tokeniter.cursor(b, t)
        for b, d in duration_items(cursor, *classes) for t in d]


