# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2013 by Wilbert Berendsen
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

import ly.document
import ly.lex.lilypond


durations = ['\\maxima', '\\longa', '\\breve',
    '1', '2', '4', '8', '16', '32', '64', '128', '256', '512', '1024', '2048']


def music_items(source, command=False, chord=False):
    """Yields lists of (block, token) tuples describing rests, skips or pitches.
    
    source is a ly.document.TokenIterator instance following the state.
    
    The following keyword arguments can be used:
    - command: whether to allow pitches in \relative, \transpose, etc.
    - chord: whether to allow pitches inside chords.
    
    """
    skip_parsers = ()
    if not command:
        skip_parsers += (ly.lex.lilypond.ParsePitchCommand,)
    if not chord:
        skip_parsers += (ly.lex.lilypond.ParseChord,)

    for token in source:
        if isinstance(source.state.parser(), skip_parsers):
            continue
        while isinstance(token, _start):
            l = [(source.block, token)]
            for token in source:
                if isinstance(token, ly.lex.Space):
                    continue
                if not isinstance(token, _stay):
                    yield l
                    break
                l.append((source.block, token))
            else:
                yield l
                break
    
    
_start = (
    ly.lex.lilypond.Rest,
    ly.lex.lilypond.Skip,
    ly.lex.lilypond.Note,
    ly.lex.lilypond.ChordEnd,
    ly.lex.lilypond.Octave,
    ly.lex.lilypond.Accidental,
    ly.lex.lilypond.OctaveCheck,
    ly.lex.lilypond.Duration,
)

_stay = _start[4:]




def duration_items(cursor, *classes):
    """Yield lists of (block, token) tuples where tokens in list are instance of *classes."""
    tokens = ly.document.TokenIterator(cursor, True)
    for items in music_items(source):
        yield [(block, token) for block, token in items if isinstance(token, classes)]

def rhythm_double(cursor):
    with cursor.document as d:
        for items in duration_items(cursor, ly.lex.lilypond.Length):
            for block, token in items:
                try:
                    i = durations.index(token)
                except ValueError:
                    continue
                if i > 0:
                    d[d.slice(block, token)] = durations[i - 1]

def rhythm_halve(cursor):
    with cursor.document as d:
        for items in duration_items(cursor, ly.lex.lilypond.Length):
            for block, token in items:
                try:
                    i = durations.index(token)
                except ValueError:
                    continue
                if i < len(durations) - 1:
                    d[d.slice(block, token)] = durations[i + 1]

def rhythm_dot(cursor):
    with cursor.document as d:
        for items in duration_items(cursor, ly.lex.lilypond.Length):
            for block, token in items:
                d[d.slice(block, token, end=0)] = "."

def rhythm_undot(cursor):
    with cursor.document as d:
        for items in duration_items(cursor, ly.lex.lilypond.Dot):
            if items:
                block, token = items[0]
                del d[d.slice(block, token)]

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
    with cursortools.Writer(cursor.document()) as w:
        for c, d in items:
            if d:
                if d == prev:
                    w.removeSelectedText(c)
                prev = d

def rhythm_implicit_per_line(cursor):
    items = duration_cursor_items(cursor)
    for c, d in items:
        break
    else:
        return
    prevblock = c.block()
    prev = d or preceding(cursor)
    with cursortools.Writer(cursor.document()) as w:
        for c, d in items:
            if c.block() != prevblock:
                if not d:
                    w.insertText(c, ''.join(prev))
                else:
                    prev = d
                prevblock = c.block()
            elif d:
                if d == prev:
                    w.removeSelectedText(c)
                prev = d

def rhythm_explicit(cursor):
    items = duration_cursor_items(cursor)
    for c, d in items:
        break
    else:
        return
    prev = d or preceding(cursor)
    with cursortools.Writer(cursor.document()) as w:
        for c, d in items:
            if d:
                prev = d
            else:
                w.insertText(c, ''.join(prev))

def rhythm_apply(cursor, mainwindow):
    durs = inputdialog.getText(mainwindow,
        _("Apply Rhythm"), _("Enter a rhythm:"),
        complete = sorted(_history),
        regexp = r'([0-9./* ]|\\breve|\\longa|\\maxima)+',
        help = "rhythm", icon = icons.get('tools-rhythm'))
    if durs and durs.split():
        _history.add(durs.strip())
        duration_source = remove_dups(itertools.cycle(durs.split()))
        with cursortools.Writer(cursor.document()) as w:
            for c, d in duration_cursor_items(cursor):
                w.insertText(c, next(duration_source))

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
    with cursortools.Writer(cursor.document()) as w:
        for c, d in duration_cursor_items(cursor):
            w.insertText(c, next(duration_source))

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


