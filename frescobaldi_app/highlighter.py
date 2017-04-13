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
The Highlighter class provides syntax highlighting and more information
about a document's contents.
"""



from PyQt5.QtGui import (
    QColor, QSyntaxHighlighter, QTextBlockUserData, QTextCharFormat,
    QTextCursor, QTextDocument)


import ly.lex
import ly.colorize

import app
import cursortools
import textformats
import metainfo
import plugin
import variables
import documentinfo


metainfo.define('highlighting', True)


def mapping(data):
    """Return a dictionary mapping token classes from ly.lex to QTextCharFormats.

    The QTextFormats are queried from the specified TextFormatData instance.
    The returned dictionary is a ly.colorize.Mapping instance.

    """
    return ly.colorize.Mapper((cls, data.textFormat(mode, style.name))
                        for mode, styles in ly.colorize.default_mapping()
                            for style in styles
                                for cls in style.classes)


def highlighter(document):
    """Return the Highlighter for this document."""
    return Highlighter.instance(document)


def highlight_mapping():
    """Return the global Mapping instance that maps token class to QTextCharFormat."""
    global _highlight_mapping
    try:
        return _highlight_mapping
    except NameError:
        _highlight_mapping = mapping(textformats.formatData('editor'))
        return _highlight_mapping


def _reset_highlight_mapping():
    """Remove the global HighlightFormats instance, so it's recreated next time."""
    global _highlight_mapping
    try:
        del _highlight_mapping
    except NameError:
        pass

app.settingsChanged.connect(_reset_highlight_mapping, -100) # before all others


class Highlighter(plugin.Plugin, QSyntaxHighlighter):
    """A QSyntaxHighlighter that can highlight a QTextDocument.

    It can be used for both generic QTextDocuments as well as
    document.Document objects. In the latter case it automatically:
    - initializes whether highlighting is enabled from the document's metainfo
    - picks the mode from the variables if they specify that

    The Highlighter automatically re-reads the highlighting settings if they
    are changed.

    """
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        self._fridge = ly.lex.Fridge()
        app.settingsChanged.connect(self.rehighlight)
        self._initialState = None
        self._highlighting = True
        self._mode = None
        self.initializeDocument()

    def initializeDocument(self):
        """This method is always called by the __init__ method.

        The default implementation does nothing for generic QTextDocuments,
        but for document.Document instances it connects to some additional
        signals to keep the mode up-to-date (reading it from the variables if
        needed) and initializes whether to enable visual highlighting from the
        document's metainfo.

        """
        document = self.document()
        if hasattr(document, 'url'):
            self._highlighting = metainfo.info(document).highlighting
            document.loaded.connect(self._resetHighlighting)
            self._mode = documentinfo.mode(document, False)
            variables.manager(document).changed.connect(self._variablesChange)

    def _variablesChange(self):
        """Called whenever the variables have changed. Checks the mode."""
        mode = documentinfo.mode(self.document(), False)
        if mode != self._mode:
            self._mode = mode
            self.rehighlight()

    def _resetHighlighting(self):
        """Switch highlighting on or off depending on saved metainfo."""
        self.setHighlighting(metainfo.info(self.document()).highlighting)

    def highlightBlock(self, text):
        """Called by Qt when the highlighting of the current line needs updating."""
        # find the state of the previous line
        prev = self.previousBlockState()
        state = self._fridge.thaw(prev)
        blank = not state and (not text or text.isspace())
        if not state:
            state = self.initialState()

        # collect and save the tokens
        tokens = tuple(state.tokens(text))
        cursortools.data(self.currentBlock()).tokens = tokens

        # if blank thus far, keep the highlighter coming back
        # because the parsing state is not yet known; else save the state
        self.setCurrentBlockState(prev - 1 if blank else self._fridge.freeze(state))

        # apply highlighting if desired
        if self._highlighting:
            setFormat = lambda f: self.setFormat(token.pos, len(token), f)
            mapping = highlight_mapping()
            for token in tokens:
                f = mapping[token]
                if f:
                    setFormat(f)

    def setHighlighting(self, enable):
        """Enable or disable highlighting."""
        changed = enable != self._highlighting
        self._highlighting = enable
        if changed:
            self.rehighlight()

    def isHighlighting(self):
        """Return whether highlighting is active."""
        return self._highlighting

    def state(self, block):
        """Return a thawed ly.lex.State() object at the *end* of the QTextBlock.

        Do not use this method directly. Instead use tokeniter.state() or
        tokeniter.state_end(), because that assures the highlighter has run
        at least once.

        """
        return self._fridge.thaw(block.userState()) or self.initialState()

    def setInitialState(self, state):
        """Force the initial state. Use None to enable auto-detection."""
        self._initialState = self._fridge.freeze(state) if state else None

    def initialState(self):
        """Return the initial State for this document."""
        if self._initialState is None:
            mode = self._mode or ly.lex.guessMode(self.document().toPlainText())
            return ly.lex.state(mode)
        return self._fridge.thaw(self._initialState)


def html_copy(cursor, scheme='editor', number_lines=False):
    """Return a new QTextDocument with highlighting set as HTML textcharformats.

    The cursor is a cursor of a document.Document instance. If the cursor
    has a selection, only the selection is put in the new document.

    If number_lines is True, line numbers are added.

    """
    data = textformats.formatData(scheme)
    doc = QTextDocument()
    doc.setDefaultFont(data.font)
    doc.setPlainText(cursor.document().toPlainText())
    if metainfo.info(cursor.document()).highlighting:
        highlight(doc, mapping(data), ly.lex.state(documentinfo.mode(cursor.document())))
    if cursor.hasSelection():
        # cut out not selected text
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        cur1 = QTextCursor(doc)
        cur1.setPosition(start, QTextCursor.KeepAnchor)
        cur2 = QTextCursor(doc)
        cur2.setPosition(end)
        cur2.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cur2.removeSelectedText()
        cur1.removeSelectedText()
    if number_lines:
        c = QTextCursor(doc)
        f = QTextCharFormat()
        f.setBackground(QColor('#eeeeee'))
        if cursor.hasSelection():
            num = cursor.document().findBlock(cursor.selectionStart()).blockNumber() + 1
            last = cursor.document().findBlock(cursor.selectionEnd())
        else:
            num = 1
            last = cursor.document().lastBlock()
        lastnum = last.blockNumber() + 1
        padding = len(format(lastnum))
        block = doc.firstBlock()
        while block.isValid():
            c.setPosition(block.position())
            c.setCharFormat(f)
            c.insertText('{0:>{1}d} '.format(num, padding))
            block = block.next()
            num += 1
    return doc


def highlight(document, mapping=None, state=None):
    """Highlight a generic QTextDocument once.

    mapping is an optional Mapping instance, defaulting to the current
    configured editor highlighting formats (returned by highlight_mapping()).
    state is an optional ly.lex.State instance. By default the text type is
    guessed.

    """
    if mapping is None:
        mapping = highlight_mapping()
    if state is None:
        state = ly.lex.guessState(document.toPlainText())
    cursor = QTextCursor(document)
    block = document.firstBlock()
    while block.isValid():
        for token in state.tokens(block.text()):
            f = mapping[token]
            if f:
                cursor.setPosition(block.position() + token.pos)
                cursor.setPosition(block.position() + token.end, QTextCursor.KeepAnchor)
                cursor.setCharFormat(f)
        block = block.next()


