# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2012 by Wilbert Berendsen
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

Durations are represented simply by lists of ly.lex.lilypond.Duration tokens.
"""

from __future__ import unicode_literals

import itertools

from PyQt4.QtGui import QTextCursor

import app
import icons
import inputdialog
import cursortools
import tokeniter
import ly.lex.lilypond
import music


durations = ['\\maxima', '\\longa', '\\breve',
    '1', '2', '4', '8', '16', '32', '64', '128', '256', '512', '1024', '2048']


_clipboard = [] # clipboard for rhythm copy and paste

_history = set() # earlier rhythms typed in apply dialog


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
    with cursortools.compress_undo(cursor):
        for c in cursors(cursor, ly.lex.lilypond.Scaling):
            c.removeSelectedText()
            
def rhythm_remove_fraction_scaling(cursor):
    with cursortools.compress_undo(cursor):
        for c in cursors(cursor, ly.lex.lilypond.Scaling):
            if '/' in c.selectedText(): 
				c.removeSelectedText()            

def rhythm_remove(cursor):
    with cursortools.compress_undo(cursor):
        for c in cursors(cursor, ly.lex.lilypond.Duration):
            c.removeSelectedText()

def rhythm_implicit(cursor):
    items = duration_cursor_items(cursor)
    for c, d in items:
        break
    else:
        return
    prev = d or preceding(cursor)
    with cursortools.Editor() as e:
        for c, d in items:
            if d:
                if d == prev:
                    e.removeSelectedText(c)
                prev = d

def rhythm_implicit_per_line(cursor):
    items = duration_cursor_items(cursor)
    for c, d in items:
        break
    else:
        return
    prevblock = c.block()
    prev = d or preceding(cursor)
    with cursortools.Editor() as e:
        for c, d in items:
            if c.block() != prevblock:
                if not d:
                    e.insertText(c, ''.join(prev))
                else:
                    prev = d
                prevblock = c.block()
            elif d:
                if d == prev:
                    e.removeSelectedText(c)
                prev = d

def rhythm_explicit(cursor):
    items = duration_cursor_items(cursor)
    for c, d in items:
        break
    else:
        return
    prev = d or preceding(cursor)
    with cursortools.Editor() as e:
        for c, d in items:
            if d:
                prev = d
            else:
                e.insertText(c, ''.join(prev))

def rhythm_apply(cursor, mainwindow):
    durs = inputdialog.getText(mainwindow,
        _("Apply Rhythm"), _("Enter a rhythm:"),
        complete = sorted(_history),
        regexp = r'([0-9./* ]|\\breve|\\longa|\\maxima)+',
        help = "rhythm", icon = icons.get('tools-rhythm'))
    if durs and durs.split():
        _history.add(durs.strip())
        duration_source = remove_dups(itertools.cycle(durs.split()))
        with cursortools.Editor() as e:
            for c, d in duration_cursor_items(cursor):
                e.insertText(c, next(duration_source))

def rhythm_copy(cursor):
    del _clipboard[:]
    for b, d in duration_items(cursor, ly.lex.lilypond.Duration):
        _clipboard.append(''.join(d))
    if _clipboard and _clipboard[0] == '':
        prec = preceding(cursor)
        if prec:
            _clipboard[0] = ''.join(prec)

def rhythm_paste(cursor):
    duration_source = itertools.cycle(_clipboard)
    with cursortools.Editor() as e:
        for c, d in duration_cursor_items(cursor):
            e.insertText(c, next(duration_source))

def remove_dups(iterable):
    old = None
    for i in iterable:
        yield '' if i == old else i
        old = i

def duration_items(cursor, *classes):
    """Yields block, list where tokens in list are instance of *classes."""
    source = tokeniter.Source.selection(cursor, True)
    for m in music.music_items(source):
        yield source.block, [token for token in m if isinstance(token, classes)]

def duration_cursor_items(cursor):
    """Yields two-tuples (cursor, list of duration tokens).
    
    The list of duration tokens may be empty. This can be used to find
    the places to insert or overwrite durations in the selected music.
    
    """
    source = tokeniter.Source.selection(cursor, True)
    for m in music.music_items(source):
        i = iter(m)
        c = QTextCursor(source.block)
        for t in i:
            if isinstance(t, ly.lex.lilypond.Duration):
                l = [t]
                c.setPosition(source.block.position() + t.pos)
                for t in i:
                    if isinstance(t, ly.lex.lilypond.Duration):
                        l.append(t)
                    elif not isinstance(t, ly.lex.Space):
                        break
                c.setPosition(source.block.position() + l[-1].end, c.KeepAnchor)
                break
        else:
            c.setPosition(source.block.position() + t.end)
            l = []
        yield c, l

def cursors(cursor, *classes):
    """Returns a list of cursors for the duration_items() with same args."""
    return [tokeniter.cursor(b, t)
        for b, d in duration_items(cursor, *classes) for t in d]

def preceding(cursor):
    """Returns a preceding duration before the cursor, or an empty list."""
    c = QTextCursor(cursor)
    c.setPosition(cursor.selectionStart())
    for tokens in back(c):
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Duration):
                l = [t]
                for t in tokens:
                    if isinstance(t, ly.lex.lilypond.Duration):
                        l.append(t)
                    elif not isinstance(t, ly.lex.Space):
                        break
                l.reverse()
                return l
    return []

def back(cursor):
    """Yields per-block token iters in backward direction from the cursor."""
    yield reversed(tokeniter.partition(cursor).left)
    block = cursor.block()
    while block.previous().isValid():
        block = block.previous()
        yield reversed(tokeniter.tokens(block))


