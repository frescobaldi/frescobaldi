# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Highlights matching tokens such as { and }, << and >> etc.
"""

import weakref

import app
import ly.tokenize
import tokeniter


_matchers = weakref.WeakKeyDictionary()

@app.mainwindowCreated.connect
def newMatcher(mainwindow):
    _matchers[mainwindow] = Matcher(mainwindow)
    

class Matcher(object):
    def __init__(self, mainwindow):
        mainwindow.currentViewChanged.connect(self.newView)
        view = mainwindow.currentView()
        if view:
            self.newView(view)
        else:
            self.view = lambda: None
        
    def newView(self, view, old=None):
        self.view = weakref.ref(view)
        if old:
            old.cursorPositionChanged.disconnect(self.checkMatches)
            old.document().contentsChange.disconnect(self.checkContentsChange)
        view.cursorPositionChanged.connect(self.checkMatches)
        view.document().contentsChange.connect(self.checkContentsChange)
    
    def checkContentsChange(self, position):
        if position == self.view().textCursor().position():
            self.checkMatches()
            
    def checkMatches(self):
        # see if there are matches
        cursor = self.view().textCursor()
        block = cursor.block()
        column = cursor.position() - block.position()
        tokens = tokeniter.TokenIterator(block)
        source = None
        for token in tokens.forward(False):
            if token.pos <= column <= token.end:
                if isinstance(token, ly.tokenize.MatchStart):
                    source, match, other = tokens.forward(), ly.tokenize.MatchStart, ly.tokenize.MatchEnd
                    break
                elif isinstance(token, ly.tokenize.MatchEnd):
                    source, match, other = tokens.backward(), ly.tokenize.MatchEnd, ly.tokenize.MatchStart
                    break
            elif token.pos > column:
                break
        if source:
            # we've found a matcher item
            cursor1 = tokens.cursor()
            nest = 0
            for token2 in source:
                if isinstance(token2, other) and token2.matchname == token.matchname:
                    if nest == 0:
                        # we've found the matching item!
                        cursor2 = tokens.cursor()
                        self.view().setMatches((cursor1, cursor2))
                        return
                    else:
                        nest -= 1
                elif isinstance(token2, match) and token2.matchname == token.matchname:
                    nest += 1
        self.view().clearMatches()


