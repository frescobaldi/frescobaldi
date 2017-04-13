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
Highlights matching tokens such as { and }, << and >> etc.
"""


import weakref

from PyQt5.QtWidgets import QAction

import app
import plugin
import ly.lex
import lydocument
import viewhighlighter
import actioncollection
import actioncollectionmanager


class AbstractMatcher(object):
    def __init__(self, view=None):
        """Initialize with an optional View. (Does not keep a reference.)"""
        self._view = lambda: None
        if view:
            self.setView(view)
        app.settingsChanged.connect(self.updateSettings)
        self.updateSettings()

    def updateSettings(self):
        from PyQt5.QtCore import QSettings
        s = QSettings()
        s.beginGroup("editor_highlighting")
        self._match_duration = s.value("match", 1, int) * 1000

    def setView(self, view):
        """Set the current View (to monitor for cursor position changes)."""
        old = self._view()
        if old:
            old.cursorPositionChanged.disconnect(self.showMatches)
        if view:
            self._view = weakref.ref(view)
            view.cursorPositionChanged.connect(self.showMatches)
        else:
            self._view = lambda: None

    def view(self):
        """Return the current View."""
        return self._view()

    def highlighter(self):
        """Implement to return an ArbitraryHighlighter for the current View."""
        pass

    def showMatches(self):
        """Highlights matching tokens if the view's cursor is at such a token."""
        cursors = matches(self.view().textCursor(), self.view())
        if cursors:
            self.highlighter().highlight("match", cursors, 2, self._match_duration)
        else:
            self.highlighter().clear("match")


class Matcher(AbstractMatcher, plugin.MainWindowPlugin):
    """One Matcher automatically handling the current View."""
    def __init__(self, mainwindow):
        super(Matcher, self).__init__()
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.view_matching_pair.triggered.connect(self.moveto_match)
        ac.view_matching_pair_select.triggered.connect(self.select_match)
        mainwindow.currentViewChanged.connect(self.setView)

        view = mainwindow.currentView()
        if view:
            self.setView(view)

    def highlighter(self):
        return viewhighlighter.highlighter(self.view())

    def moveto_match(self):
        """Jump to the matching token."""
        self.goto_match(False)

    def select_match(self):
        """Select from the current to the matching token."""
        self.goto_match(True)

    def goto_match(self, select=False):
        """Jump to the matching token, selecting the text if select is True."""
        cursor = self.view().textCursor()
        cursors = matches(cursor)
        if len(cursors) < 2:
            return
        if select:
            if cursors[0] < cursors[1]:
                anchor, pos = cursors[0].selectionStart(), cursors[1].selectionEnd()
            else:
                anchor, pos = cursors[0].selectionEnd(), cursors[1].selectionStart()
            cursor.setPosition(anchor)
            cursor.setPosition(pos, cursor.KeepAnchor)
        else:
            cursor.setPosition(cursors[1].selectionStart())
        self.view().setTextCursor(cursor)


class Actions(actioncollection.ActionCollection):
    name = "matchingpair"
    def createActions(self, parent):
        self.view_matching_pair = QAction(parent)
        self.view_matching_pair_select = QAction(parent)

    def translateUI(self):
        self.view_matching_pair.setText(_("Matching Pai&r"))
        self.view_matching_pair_select.setText(_("&Select Matching Pair"))


def matches(cursor, view=None):
    """Return a list of zero to two cursors specifying matching tokens.

    If the list is empty, the cursor was not at a MatchStart/MatchEnd token,
    if the list only contains one cursor the matching token could not be found,
    if the list contains two cursors, the first is the token the cursor was at,
    and the second is the matching token.

    If view is given, only the visible part of the document is searched.

    """
    block = cursor.block()
    column = cursor.position() - block.position()
    tokens = lydocument.Runner(lydocument.Document(cursor.document()))
    tokens.move_to_block(block)

    if view is not None:
        first_block = view.firstVisibleBlock()
        bottom = view.contentOffset().y() + view.viewport().height()
        pred_forward = lambda: view.blockBoundingGeometry(tokens.block).top() <= bottom
        pred_backward = lambda: tokens.block >= first_block
    else:
        pred_forward = lambda: True
        pred_backward = lambda: True

    source = None
    for token in tokens.forward_line():
        if token.pos <= column <= token.end:
            if isinstance(token, ly.lex.MatchStart):
                match, other = ly.lex.MatchStart, ly.lex.MatchEnd
                def source_gen():
                    while pred_forward():
                        for t in tokens.forward_line():
                            yield t
                        if not tokens.next_block():
                            break
                source = source_gen()
                break
            elif isinstance(token, ly.lex.MatchEnd):
                match, other = ly.lex.MatchEnd, ly.lex.MatchStart
                def source_gen():
                    while pred_backward():
                        for t in tokens.backward_line():
                            yield t
                        if not tokens.previous_block():
                            break
                source = source_gen()
                break
        elif token.pos > column:
            break
    cursors = []
    if source:
        # we've found a matcher item
        cursors.append(tokens.cursor())
        nest = 0
        for token2 in source:
            if isinstance(token2, other) and token2.matchname == token.matchname:
                if nest == 0:
                    # we've found the matching item!
                    cursors.append(tokens.cursor())
                    break
                else:
                    nest -= 1
            elif isinstance(token2, match) and token2.matchname == token.matchname:
                nest += 1
    return cursors



app.mainwindowCreated.connect(Matcher.instance)

