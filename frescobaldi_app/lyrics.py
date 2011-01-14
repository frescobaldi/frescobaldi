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
Commands for manipulating Lyrics.
"""

import re

from PyQt4.QtGui import QAction, QApplication, QTextCursor

import ly.tokenize.lilypond
import actioncollection
import plugin
import tokeniter


# regexp to match a lyric word
_word_re = re.compile(r"[^\W0-9_]+")


def lyrics(mainwindow):
    return Lyrics.instance(mainwindow)
    

class Lyrics(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        mainwindow.addActionCollection(ac)
        
        ac.lyrics_hyphenate.triggered.connect(self.hyphenate)
        ac.lyrics_dehyphenate.triggered.connect(self.dehyphenate)
        ac.lyrics_copy_dehyphenated.triggered.connect(self.copy_dehyphenated)
        
        mainwindow.currentViewChanged.connect(self.slotViewChanged)
        
    def slotViewChanged(self, view, old):
        if old:
            old.selectionChanged.disconnect(self.updateActions)
        view.selectionChanged.connect(self.updateActions)
        self.updateActions()
        
    def updateActions(self):
        selection = self.mainwindow().currentView().textCursor().hasSelection()
        self.actionCollection.lyrics_hyphenate.setEnabled(selection)
        self.actionCollection.lyrics_dehyphenate.setEnabled(selection)
        self.actionCollection.lyrics_copy_dehyphenated.setEnabled(selection)
    
    def hyphenate(self):
        """Hyphenates selected Lyrics text."""
        view = self.mainwindow().currentView()
        cursor = view.textCursor()
        found = []
        # find text to hyphenate
        for block, tokens in tokeniter.selectedTokens(cursor):
            for token in tokens:
                if isinstance(token, ly.tokenize.lilypond.LyricText):
                    # a word found
                    m = _word_re.search(token)
                    if m:
                        found.append((tokeniter.cursor(block, token, m.start(), m.end()), m.group()))
        if not found:
            # no tokens were found, then tokenize the text again as if in lyricmode
            start = cursor.selectionStart()
            state = ly.tokenize.State(ly.tokenize.lilypond.LilyPondParserLyricMode)
            for token in state.tokens(cursor.selection().toPlainText()):
                if isinstance(token, ly.tokenize.lilypond.LyricText):
                    # a word found
                    m = _word_re.search(token)
                    if m:
                        cur = QTextCursor(cursor)
                        cur.setPosition(start + token.pos + m.start())
                        cur.setPosition(start + token.pos + m.end(), QTextCursor.KeepAnchor)
                        found.append((cur, m.group()))
        if not found:
            # still not succeeded, then try flat text
            for m in _word_re.finditer(cursor.selection().toPlainText()):
                cur = QTextCursor(cursor)
                cur.setPosition(start + m.start())
                cur.setPosition(start + m.end(), QTextCursor.KeepAnchor)
                found.append((cur, m.group()))
        if found:
            import hyphendialog
            h = hyphendialog.HyphenDialog(self.mainwindow()).hyphenator()
            if h:
                with tokeniter.keepSelection(cursor):
                    with tokeniter.editBlock(cursor):
                        for cur, word in found:
                            hyph_word = h.inserted(word, ' -- ')
                            if word != hyph_word:
                                cur.insertText(hyph_word)
            
    def dehyphenate(self):
        """De-hyphenates selected Lyrics text."""
        view = self.mainwindow().currentView()
        cursor = view.textCursor()
        text = cursor.selection().toPlainText()
        if ' --' in text:
            with tokeniter.keepSelection(cursor):
                cursor.insertText(self.removehyphens(text))
            view.setTextCursor(cursor)
            
    def copy_dehyphenated(self):
        """Copies selected lyrics text to the clipboard with hyphenation removed."""
        text = self.mainwindow().currentView().textCursor().selection().toPlainText()
        QApplication.clipboard().setText(self.removehyphens(text))
        
    def removehyphens(self, text):
        """Removes hyphens and extenders from text."""
        return re.sub(r"[ \t]*--[ \t]*|__[ \t]*|_([ \t]+_)*[ \t]*", '', text)
    

class Actions(actioncollection.ActionCollection):
    name = "lyrics"
    
    def createActions(self, parent=None):
        
        self.lyrics_hyphenate = QAction(parent)
        self.lyrics_dehyphenate = QAction(parent)
        self.lyrics_copy_dehyphenated = QAction(parent)
        
        
    def translateUI(self):
        self.lyrics_hyphenate.setText(_("Hyphenate Lyrics Text"))
        self.lyrics_dehyphenate.setText(_("Remove hyphenation"))
        self.lyrics_copy_dehyphenated.setText(_("Copy Lyrics with hyphenation removed"))
        

