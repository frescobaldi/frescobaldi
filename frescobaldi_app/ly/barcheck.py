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

import collections
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


class event(object):
    """A limited event type at a certain time."""
    def __init__(self):
        self._nodes = []
        self.cadenza = None
        self.barcheck = False
        self.timesig = None
        self.partial = None
    
    def append(self, node):
        self._nodes.append(node)

    def __repr__(self):
        s = []
        if self.cadenza is not None:
            s.append('cadenza' + ('On' if self.cadenza else 'Off'))
        if self.barcheck:
            s.append('bar')
        if self.timesig is not None:
            s.append('T{0}'.format(self.timesig))
        if self.partial is not None:
            s.append('P{0}'.format(self.partial))
        if self._nodes:
            s.append(repr(self._nodes))
        return '<event {0}>'.format(' '.join(s))


def insert(cursor, music=None):
    """Insert bar checks within the selected range."""
    if music is None:
        import ly.music
        music = ly.music.document(cursor.document)
    
    if len(music) == 0:
        return
    
    if cursor.start:
        n = music.node(cursor.start, 1)
        nodes = itertools.chain((n,), n.forward())
    else:
        nodes = music
    if cursor.end is None:
        iter_nodes = iter
    else:
        predicate = lambda node: node.position < cursor.end
        def iter_nodes(it):
            return itertools.takewhile(predicate, it)
    
    # make time-based lists of events
    event_lists = []
    
    def do_topnode(node):
        if not isinstance(node, ly.music.items.Music):
            for n in node:
                do_topnode(n)
            return
        
        def do_node(node, time, scaling):
            if isinstance(node, (ly.music.items.Durable, ly.music.items.UserCommand)):
                if node.position >= cursor.start:
                    events[time].append(node)
                time += node.length() * scaling
            elif isinstance(node, ly.music.items.TimeSignature):
                events[time].timesig = node.measure_length()
            elif isinstance(node, ly.music.items.Partial):
                events[time].partial = node.length()
            elif isinstance(node, ly.music.items.PipeSymbol):
                events[time].barcheck = True
            elif isinstance(node, ly.music.items.Command) and node.token in (
                    'cadenzaOn', 'cadenzaOff'):
                events[time].cadenza = node.token == 'cadenzaOn'
            elif isinstance(node, ly.music.items.Grace):
                pass
            elif isinstance(node, ly.music.items.LyricMode):
                pass
            elif isinstance(node, ly.music.items.MusicList) and node.simultaneous:
                time = max(do_node(n, time, scaling) for n in iter_nodes(node))
            elif isinstance(node, ly.music.items.Music):
                if isinstance(node, ly.music.items.Scaler):
                    scaling *= node.scaling
                for n in iter_nodes(node):
                    time = do_node(n, time, scaling)
            else:
                do_topnode(node)
            return time
        
        events = collections.defaultdict(event)
        do_node(node, 0, 1)
        event_lists.append(sorted(events.items()))
    
    do_topnode(nodes)
    
    for event_list in event_lists:
        
        # default to 4/4 without pickup
        measure_length = 1
        measure_pos = 0
        
        for time, evt in event_list:
            print(time, evt)


