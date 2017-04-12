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
The Quick Insert panel dynamics Tool.
"""


from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QHBoxLayout, QToolButton

import app
import icons
import symbols
import cursortools
import tokeniter
import lydocument
import ly.document
import ly.lex.lilypond
import ly.rhythm
import documentactions

from . import tool
from . import buttongroup


class Dynamics(tool.Tool):
    """Dynamics tool in the quick insert panel toolbox."""
    def __init__(self, panel):
        super(Dynamics, self).__init__(panel)
        self.removemenu = QToolButton(self,
            autoRaise=True,
            popupMode=QToolButton.InstantPopup,
            icon=icons.get('edit-clear'))

        mainwindow = panel.parent().mainwindow()
        mainwindow.selectionStateChanged.connect(self.removemenu.setEnabled)
        self.removemenu.setEnabled(mainwindow.hasSelection())

        ac = documentactions.DocumentActions.instance(mainwindow).actionCollection
        self.removemenu.addAction(ac.tools_quick_remove_dynamics)

        layout = QHBoxLayout()
        layout.addWidget(self.removemenu)
        layout.addStretch(1)

        self.layout().addLayout(layout)
        self.layout().addWidget(DynamicGroup(self))
        self.layout().addWidget(SpannerGroup(self))
        self.layout().addStretch(1)

    def icon(self):
        """Should return an icon for our tab."""
        return symbols.icon("dynamic_f")

    def title(self):
        """Should return a title for our tab."""
        return _("Dynamics")

    def tooltip(self):
        """Returns a tooltip"""
        return _("Dynamic symbols.")


class Group(buttongroup.ButtonGroup):
    """Base class for dynamic button groups with insert implementation."""
    def actionTriggered(self, name):
        name = name[8:]
        direction = ['_', '', '^'][self.direction() + 1]
        isSpanner = name not in dynamic_marks
        if isSpanner:
            dynamic = dynamic_spanners[name]
        else:
            dynamic = '\\' + name
        cursor = self.mainwindow().textCursor()
        if not cursor.hasSelection():
            # dynamic right before the cursor?
            left = tokeniter.partition(cursor).left
            if not left or not isinstance(left[-1], ly.lex.lilypond.Dynamic):
                # no, find the first pitch
                c = lydocument.cursor(cursor)
                c.end = None
                for item in ly.rhythm.music_items(c, partial=ly.document.OUTSIDE):
                    cursor.setPosition(item.end)
                    break
            cursor.insertText(direction + dynamic)
            self.mainwindow().currentView().setTextCursor(cursor)
        else:
            c = lydocument.cursor(cursor)
            cursors = []
            for item in ly.rhythm.music_items(c):
                csr = QTextCursor(cursor.document())
                csr.setPosition(item.end)
                cursors.append(csr)
            if not cursors:
                return
            c1, c2 = cursors[0], cursors[-1]
            # are there dynamics at the cursor? then skip them
            d1 = dynamics(c1)
            if d1:
                c1 = tokeniter.cursor(c1.block(), d1[-1], start=len(d1[-1]))
            with cursortools.compress_undo(cursor):
                if len(cursors) > 1:
                    # dynamics after the end cursor?
                    d2 = dynamics(c2)
                    if isSpanner and not d2:
                        # don't terminate the spanner if there's a dynamic there
                        c2.insertText('\\!')
                    elif set(d1).intersection(dynamic_spanners.values()):
                        # write the dynamic at the end if there's a spanner at start
                        # remove ending \! if there
                        terminator = tokeniter.find("\\!", d2)
                        if terminator:
                            c2 = tokeniter.cursor(c2.block(), terminator)
                        if direction in d1:
                            c2.insertText(dynamic)
                        else:
                            c2.insertText(direction + dynamic)
                        return
                c1.insertText(direction + dynamic)


class DynamicGroup(Group):
    def translateUI(self):
        # L10N: dynamic signs
        self.setTitle(_("Signs"))

    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for m in dynamic_marks:
            name = 'dynamic_' + m
            yield name, symbols.icon(name), None

    def actionTexts(self):
        """Should yield name, text for very action."""
        for m in dynamic_marks:
            name = 'dynamic_' + m
            bold = "<b><i>{0}</i></b>".format
            yield name, _("Dynamic sign {name}").format(name=bold(m))


class SpannerGroup(Group):
    def translateUI(self):
        self.setTitle(_("Spanners"))

    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None

    def actionTexts(self):
        """Should yield name, text for very action."""
        yield 'dynamic_hairpin_cresc', _("Hairpin crescendo")
        yield 'dynamic_cresc', _("Crescendo")
        yield 'dynamic_hairpin_dim', _("Hairpin diminuendo")
        yield 'dynamic_dim', _("Diminuendo")
        yield 'dynamic_decresc', _("Decrescendo")


def dynamics(cursor):
    """Returns a tuple of dynamic tokens (including _ or ^) at the cursor."""
    right = tokeniter.partition(cursor).right
    i = 0
    for j, t in enumerate(right, 1):
        if isinstance(t, ly.lex.lilypond.Dynamic):
            i = j
        elif not isinstance(t, (ly.lex.Space, ly.lex.lilypond.Direction)):
            break
    return right[:i]


dynamic_marks = (
    'f', 'ff', 'fff', 'ffff', 'fffff',
    'p', 'pp', 'ppp', 'pppp', 'ppppp',
    'mf', 'mp', 'fp', 'sfz', 'rfz',
    'sf', 'sff', 'sp', 'spp',
)

dynamic_spanners = {
    'hairpin_cresc': '\\<',
    'hairpin_dim':   '\\>',
    'cresc':         '\\cresc',
    'decresc':       '\\decresc',
    'dim':           '\\dim',
}


