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
The Quick Insert panel spanners Tool.
"""

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QHBoxLayout, QToolButton

import icons
import cursortools
import tokeniter
import lydocument
import documentactions
import symbols
import ly.document
import ly.rhythm
from ly.lex.lilypond import Note, ChordStart, Rest, Skip, Duration

from . import tool
from . import buttongroup


class Spanners(tool.Tool):
    """Dynamics tool in the quick insert panel toolbox."""

    def __init__(self, panel):
        super(Spanners, self).__init__(panel)
        self.removemenu = QToolButton(self,
                                      autoRaise=True,
                                      popupMode=QToolButton.InstantPopup,
                                      icon=icons.get('edit-clear'))

        mainwindow = panel.parent().mainwindow()
        mainwindow.selectionStateChanged.connect(self.removemenu.setEnabled)
        self.removemenu.setEnabled(mainwindow.hasSelection())

        ac = documentactions.DocumentActions.instance(mainwindow).actionCollection
        self.removemenu.addAction(ac.tools_quick_remove_slurs)
        self.removemenu.addAction(ac.tools_quick_remove_beams)
        self.removemenu.addAction(ac.tools_quick_remove_ligatures)

        layout = QHBoxLayout()
        layout.addWidget(self.removemenu)
        layout.addStretch(1)

        self.layout().addLayout(layout)
        self.layout().addWidget(ArpeggioGroup(self))
        self.layout().addWidget(GlissandoGroup(self))
        self.layout().addWidget(SpannerGroup(self))
        self.layout().addWidget(GraceGroup(self))
        self.layout().addStretch(1)

    def icon(self):
        """Should return an icon for our tab."""
        return symbols.icon("spanner_phrasingslur")

    def title(self):
        """Should return a title for our tab."""
        return _("Spanners")

    def tooltip(self):
        """Returns a tooltip"""
        return _("Slurs, spanners, etcetera.")


class ArpeggioGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Arpeggios"))

    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None

    def actionTexts(self):
        """Should yield name, text for every action."""
        yield 'arpeggio_normal', _("Arpeggio")
        yield 'arpeggio_arrow_up', _("Arpeggio with Up Arrow")
        yield 'arpeggio_arrow_down', _("Arpeggio with Down Arrow")
        yield 'arpeggio_bracket', _("Bracket Arpeggio")
        yield 'arpeggio_parenthesis', _("Parenthesis Arpeggio")

    def actionTriggered(self, name):
        # convert arpeggio_normal to arpeggioNormal, etc.
        name = _arpeggioTypes[name]
        cursor = self.mainwindow().textCursor()
        # which arpeggio type is last used?
        lastused = '\\arpeggioNormal'
        types = set(_arpeggioTypes.values())
        block = cursor.block()
        while block.isValid():
            s = types.intersection(tokeniter.tokens(block))
            if s:
                lastused = s.pop()
                break
            block = block.previous()
        # where to insert
        c = lydocument.cursor(cursor)
        c.select_end_of_block()
        with cursortools.compress_undo(cursor):
            for item in ly.rhythm.music_items(c, partial=ly.document.OUTSIDE):
                c = QTextCursor(cursor.document())
                c.setPosition(item.end)
                c.insertText('\\arpeggio')
                if name != lastused:
                    cursortools.strip_indent(c)
                    indent = c.block().text()[:c.position() - c.block().position()]
                    c.insertText(name + '\n' + indent)
                # just pick the first place
                return


class GlissandoGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Glissandos"))

    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None

    def actionTexts(self):
        """Should yield name, text for very action."""
        yield 'glissando_normal', _("Glissando")
        yield 'glissando_dashed', _("Dashed Glissando")
        yield 'glissando_dotted', _("Dotted Glissando")
        yield 'glissando_zigzag', _("Zigzag Glissando")
        yield 'glissando_trill', _("Trill Glissando")

    def actionTriggered(self, name):
        cursor = self.mainwindow().textCursor()
        style = _glissandoStyles[name]
        c = lydocument.cursor(cursor)
        c.select_end_of_block()
        for item in ly.rhythm.music_items(c, partial=ly.document.OUTSIDE):
            c = QTextCursor(cursor.document())
            c.setPosition(item.end)
            if style:
                text = "-\\tweak #'style #'{0} \\glissando".format(style)
            else:
                text = '\\glissando'
            c.insertText(text)
            return


class SpannerGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Spanners"))

    def actionData(self):
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None

    def actionTexts(self):
        yield 'spanner_slur', _("Slur")
        yield 'spanner_phrasingslur', _("Phrasing Slur")
        yield 'spanner_beam16', _("Beam")
        yield 'spanner_trill', _("Trill")
        yield 'spanner_melisma', _("Melisma")

    def actionTriggered(self, name):
        cursor = self.mainwindow().textCursor()
        positions = None

        d = ['_', '', '^'][self.direction() + 1]
        if name == "spanner_slur":
            spanner = d + '(', ')'
        elif name == "spanner_phrasingslur":
            spanner = d + '\\(', '\\)'
        elif name == "spanner_beam16":
            spanner = d + '[', ']'
        elif name == "spanner_trill":
            spanner = '\\startTrillSpan', '\\stopTrillSpan'
        elif name == "spanner_melisma":
            spanner = '\\melisma', '\\melismaEnd'
            positions = melisma_positions(cursor)

        positions = positions or spanner_positions(cursor)

        with cursortools.compress_undo(cursor):
            for s, c in zip(spanner, positions):
                c.insertText(s)


class GraceGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Grace Notes"))

    def actionData(self):
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None

    def actionTexts(self):
        yield 'grace_grace', _("Grace Notes")
        yield 'grace_beam', _("Grace Notes w. beaming")
        yield 'grace_accia', _("Acciaccatura")
        yield 'grace_appog', _("Appoggiatura")
        yield 'grace_slash', _("Slashed no slur")
        yield 'grace_after', _("After grace")

    def actionTriggered(self, name):
        d = ['_', '', '^'][self.direction() + 1]
        single = ''
        if name == "grace_grace":
            inner = ''
            outer = '\\grace { ', ' }'
            single = '\\grace '
        elif name == "grace_beam":
            inner = d + '[', ']'
            outer = '\\grace { ', ' }'
        elif name == "grace_accia":
            inner = ''
            outer = '\\acciaccatura { ', ' }'
            single = '\\acciaccatura '
        elif name == "grace_appog":
            inner = ''
            outer = '\\appoggiatura { ', ' }'
            single = '\\appoggiatura '
        elif name == "grace_slash":
            inner = d + '[', ']'
            outer = '\\slashedGrace { ', ' }'
        elif name == "grace_after":
            inner = d + '{ '
            outer = '\\afterGrace ', ' }'

        cursor = self.mainwindow().textCursor()
        with cursortools.compress_undo(cursor):
            if inner:
                for i, ci in zip(inner, spanner_positions(cursor, name)):
                    ci.insertText(i)
            if cursor.hasSelection():
                ins = self.mainwindow().textCursor()
                ins.setPosition(cursor.selectionStart())
                ins.insertText(outer[0])
                ins.setPosition(cursor.selectionEnd())
                ins.insertText(outer[1])
            else:
                if single:
                    cursor.insertText(single)
                else:
                    c = lydocument.cursor(cursor)
                    c.end = None
                    items = list(ly.rhythm.music_items(c, partial=ly.document.OUTSIDE))
                    after = self.mainwindow().textCursor()
                    try:
                        i = items[2]
                        pos = i.pos + 1
                        end = (i.tokens or i.dur_tokens)[0].end
                        after.setPosition(pos)
                        after.setPosition(end, QTextCursor.KeepAnchor)
                    except IndexError:
                        after.movePosition(cursor.EndOfLine)
                    after.insertText(outer[1])
                    cursor.insertText(outer[0])


def spanner_positions(cursor):
    """Return a list with 0 to 2 QTextCursor instances.

    At the first cursor a starting spanner item can be inserted, at the
    second an ending item.
    """
    c = lydocument.cursor(cursor)
    if cursor.hasSelection():
        partial = ly.document.INSIDE
    else:
        # just select until the end of the current line
        c.select_end_of_block()
        partial = ly.document.OUTSIDE

    items = list(ly.rhythm.music_items(c, partial=partial))

    if cursor.hasSelection():
        del items[1:-1]
    else:
        del items[2:]

    positions = []
    for i in items:
        c = QTextCursor(cursor.document())
        c.setPosition(i.end)
        positions.append(c)
    return positions


def melisma_positions(cursor: QTextCursor) -> list:
    """ Return the correct positions of the melisma commands, after all spanners already inserted after the note """

    def search_spanners_symbols(item1, item2, spanners) -> int:
        """Find the spanners in the list lying between two music items.
        :param item1: First item
        :param item2: Second item
        :param spanners: A list of spanners to be examined
        :return: The position in the document of the last spanner attached to the first item, or None if nothing is found
        """

        last = None
        for span in spanners:
            if span[1] < item2.pos and span[0] >= item1.end:
                last = span[1]
        return last

    crs = lydocument.cursor(cursor)
    if cursor.hasSelection():
        partial = ly.document.INSIDE
    else:
        # just select until the end of the current line
        crs.select_end_of_block()
        partial = ly.document.OUTSIDE

    items = list(ly.rhythm.music_items(crs, partial=partial))

    # only one item at the end of a block
    if len(items) == 1:
        return []

    if cursor.hasSelection():
        # get the music item next to the selection end (used to search for spanner symbols after the selection)
        tk = next_music_token(crs.document, items[-1].end)
        items.append(tk or _item(crs.end))
        crs.select_end_of_block()  # need for search all spanners outside the selection
    else:
        del items[3:]  # leave at most 3 items
        if len(items) < 3:
            items.append(_item(crs.end))

    # get all spanners from start up to last item
    positions = get_spanners_in_range(crs.document, items[0].end, items[-1].pos)

    a = search_spanners_symbols(items[0], items[1], positions) or items[0].end  # spanners between item0 and item1
    b = search_spanners_symbols(items[-2], items[-1], positions) or items[-2].end  # spanners between the last two items

    positions = []
    for i in [a, b]:
        c = QTextCursor(cursor.document())
        c.setPosition(i)
        positions.append(c)
    return positions


def _item(pos: int, end=None):
    """Shorthand to get an empty music-item carrying positional information"""
    return ly.rhythm.music_item(None, None, None, None, pos, end or pos)


def next_music_token(doc, pos):
    """
    Return a music_item with its positions in the document next to the index. It identifies only the
    start of a music item (Note, Rest, Skip, Chord), without collect all subsequent tokens (durations,
    closing chords...)
    :param doc: a lilypond document
    :param pos: int indicating a position in the document
    :return: (token.pos, token.end)
    """
    cursor = ly.document.Cursor(doc, pos)
    source = ly.document.Source(cursor, True, ly.document.INSIDE, True)

    for token in source:
        if token.pos >= pos:
            if isinstance(token, Note) or isinstance(token, Rest) \
                    or isinstance(token, Skip) or isinstance(token, ChordStart) \
                    or isinstance(token, Duration):  # isolated durations with implied pitch
                return _item(token.pos, token.end)


def get_spanners_in_range(doc, pos, max_offset=1e5) -> list:
    """ Find all spanner symbols from pos to max_offset (or the end of the document) """
    from ly.lex.lilypond import BeamStart, BeamEnd, SlurStart, SlurEnd, PhrasingSlurStart, PhrasingSlurEnd, Command
    cursor = ly.document.Cursor(doc, pos)
    source = ly.document.Source(cursor, True, ly.document.INSIDE, True)

    positions = []
    for token in source:
        if token.pos >= max_offset:
            break
        if isinstance(token, Command):
            if token.startswith('\\startTrillSpan') or token.startswith('\\stopTrillSpan'):
                positions.append((token.pos, token.end))
        elif isinstance(token, BeamStart) \
                or isinstance(token, BeamEnd) \
                or isinstance(token, SlurStart) \
                or isinstance(token, SlurEnd) \
                or isinstance(token, PhrasingSlurStart) \
                or isinstance(token, PhrasingSlurEnd):
            positions.append((token.pos, token.end))
    return positions


_arpeggioTypes = {
    'arpeggio_normal': '\\arpeggioNormal',
    'arpeggio_arrow_up': '\\arpeggioArrowUp',
    'arpeggio_arrow_down': '\\arpeggioArrowDown',
    'arpeggio_bracket': '\\arpeggioBracket',
    'arpeggio_parenthesis': '\\arpeggioParenthesis',
}

_glissandoStyles = {
    'glissando_normal': '',
    'glissando_dashed': 'dashed-line',
    'glissando_dotted': 'dotted-line',
    'glissando_zigzag': 'zigzag',
    'glissando_trill': 'trill',
}
