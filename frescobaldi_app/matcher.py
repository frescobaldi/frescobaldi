# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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

from __future__ import unicode_literals

import weakref

import app
import plugin
import ly.lex
import tokeniter
import viewhighlighter


class AbstractMatcher(object):
    def __init__(self, view=None):
        """Initialize with an optional View. (Does not keep a reference.)"""
        self._view = lambda: None
        if view:
            self.setView(view)
    
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
        cursor = self.view().textCursor()
        block = cursor.block()
        column = cursor.position() - block.position()
        tokens = tokeniter.Runner(block)
        source = None
        for token in tokens.forward_line():
            if token.pos <= column <= token.end:
                if isinstance(token, ly.lex.MatchStart):
                    match, other = ly.lex.MatchStart, ly.lex.MatchEnd
                    bottom = self.view().contentOffset().y() + self.view().viewport().height()
                    def source_gen():
                        while self.view().blockBoundingGeometry(tokens.block).top() <= bottom:
                            for t in tokens.forward_line():
                                yield t
                            tokens.__init__(tokens.block.next())
                    source = source_gen()
                    break
                elif isinstance(token, ly.lex.MatchEnd):
                    match, other = ly.lex.MatchEnd, ly.lex.MatchStart
                    first_block = self.view().firstVisibleBlock()
                    def source_gen():
                        while tokens.block >= first_block:
                            for t in tokens.backward_line():
                                yield t
                            tokens.__init__(tokens.block.previous(), True)
                    source = source_gen()
                    break
            elif token.pos > column:
                break
        if source:
            # we've found a matcher item
            cursors = [tokens.cursor()]
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
            self.highlighter().highlight("match", cursors, 2, 1000)
        else:
            self.highlighter().clear("match")


class Matcher(AbstractMatcher, plugin.MainWindowPlugin):
    """One Matcher automatically handling the current View."""
    def __init__(self, mainwindow):
        super(Matcher, self).__init__()
        mainwindow.currentViewChanged.connect(self.setView)
        view = mainwindow.currentView()
        if view:
            self.setView(view)
        
    def highlighter(self):
        return viewhighlighter.highlighter(self.view())


app.mainwindowCreated.connect(Matcher.instance)

