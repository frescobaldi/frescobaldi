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
Commands for manipulating Lyrics.
"""


import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QTextCursor
from PyQt5.QtWidgets import QAction, QApplication

import ly.lex.lilypond
import actioncollection
import actioncollectionmanager
import plugin
import cursortools
import lydocument


# regexp to match a lyric word
_word_re = re.compile(r"[^\W0-9_]+", re.UNICODE)


def lyrics(mainwindow):
    return Lyrics.instance(mainwindow)


class Lyrics(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.lyrics_hyphenate.triggered.connect(self.hyphenate)
        ac.lyrics_dehyphenate.triggered.connect(self.dehyphenate)
        ac.lyrics_copy_dehyphenated.triggered.connect(self.copy_dehyphenated)
        mainwindow.selectionStateChanged.connect(self.updateSelection)
        self.updateSelection(mainwindow.hasSelection())

    def updateSelection(self, selection):
        self.actionCollection.lyrics_dehyphenate.setEnabled(selection)
        self.actionCollection.lyrics_copy_dehyphenated.setEnabled(selection)

    def hyphenate(self):
        """Hyphenates selected Lyrics text."""
        view = self.mainwindow().currentView()
        cursor = view.textCursor()
        found = []
        c = lydocument.cursor(cursor, select_all=True)
        # find text to hyphenate
        source = lydocument.Source(c)
        for token in source:
            if isinstance(token, ly.lex.lilypond.LyricText):
                # a word found
                pos = source.position(token)
                for m in _word_re.finditer(token):
                    found.append((pos + m.start(), pos + m.end(), m.group()))
        if not found and cursor.hasSelection():
            # no tokens were found, then tokenize the text again as if in lyricmode
            start = cursor.selectionStart()
            state = ly.lex.State(ly.lex.lilypond.ParseLyricMode)
            for token in state.tokens(cursor.selection().toPlainText()):
                if isinstance(token, ly.lex.lilypond.LyricText):
                    # a word found
                    pos = start + token.pos
                    for m in _word_re.finditer(token):
                        found.append((pos + m.start(), pos + m.end(), m.group()))
        if not found and cursor.hasSelection():
            # still not succeeded, then try flat text
            for m in _word_re.finditer(cursor.selection().toPlainText()):
                found.append((start + m.start(), start + m.end(), m.group()))
        if found:
            import hyphendialog
            h = hyphendialog.HyphenDialog(self.mainwindow()).hyphenator()
            if h:
                with c.document as d:
                    for start, end, word in found:
                        hyph_word = h.inserted(word, ' -- ')
                        if word != hyph_word:
                            d[start:end] = hyph_word

    def dehyphenate(self):
        """De-hyphenates selected Lyrics text."""
        view = self.mainwindow().currentView()
        cursor = view.textCursor()
        text = cursor.selection().toPlainText()
        if ' --' in text:
            with cursortools.keep_selection(cursor, view):
                cursor.insertText(removehyphens(text))

    def copy_dehyphenated(self):
        """Copies selected lyrics text to the clipboard with hyphenation removed."""
        text = self.mainwindow().textCursor().selection().toPlainText()
        QApplication.clipboard().setText(removehyphens(text))


class Actions(actioncollection.ActionCollection):
    name = "lyrics"

    def createActions(self, parent=None):

        self.lyrics_hyphenate = QAction(parent)
        self.lyrics_dehyphenate = QAction(parent)
        self.lyrics_copy_dehyphenated = QAction(parent)

        self.lyrics_hyphenate.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_L))

    def translateUI(self):
        self.lyrics_hyphenate.setText(_("&Hyphenate Lyrics Text..."))
        self.lyrics_dehyphenate.setText(_("&Remove hyphenation"))
        self.lyrics_copy_dehyphenated.setText(_("&Copy Lyrics with hyphenation removed"))


def removehyphens(text):
    """Removes hyphens and extenders from text."""
    text = re.sub(r"[ \t]*--[ \t]*|__[ \t]*|_[ \t]+(_[ \t]+)*", '', text)
    return text.replace('_', ' ').replace('~', ' ')


