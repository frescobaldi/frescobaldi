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

from __future__ import unicode_literals


from PyQt4.QtGui import (
    QSyntaxHighlighter, QTextBlockUserData, QTextCursor, QTextDocument)


import ly.lex
import ly.lex.lilypond
import ly.lex.scheme
import ly.lex.html
import ly.lex.texinfo

import app
import cursortools
import textformats
import metainfo
import plugin
import variables
import documentinfo


metainfo.define('highlighting', True)


def mapping(data):
    """Return a dictionary mapping token classes from ly.lex to QTextFormats.
    
    The QTextFormats are queried from the specified TextFormatData instance.
    
    """
    return {
    
        # LilyPond
        ly.lex.lilypond.Keyword: data.textFormat('lilypond', 'keyword'),
        ly.lex.lilypond.Command: data.textFormat('lilypond', 'command'),
        ly.lex.lilypond.Dynamic: data.textFormat('lilypond', 'dynamic'),
        ly.lex.lilypond.MusicItem: data.textFormat('lilypond', 'pitch'),
        ly.lex.lilypond.Skip: data.textFormat('lilypond', 'command'),
        ly.lex.lilypond.Octave: data.textFormat('lilypond', 'octave'),
        ly.lex.lilypond.Duration: data.textFormat('lilypond', 'duration'),
        ly.lex.lilypond.OctaveCheck: data.textFormat('lilypond', 'check'),
        ly.lex.lilypond.Direction: data.textFormat('lilypond', 'articulation'),
        ly.lex.lilypond.Fingering: data.textFormat('lilypond', 'fingering'),
        ly.lex.lilypond.StringNumber: data.textFormat('lilypond', 'stringnumber'),
        ly.lex.lilypond.Articulation: data.textFormat('lilypond', 'articulation'),
        ly.lex.lilypond.Slur: data.textFormat('lilypond', 'slur'),
        ly.lex.lilypond.Chord: data.textFormat('lilypond', 'chord'),
        ly.lex.lilypond.ChordItem: data.textFormat('lilypond', 'chord'),
        ly.lex.lilypond.PipeSymbol: data.textFormat('lilypond', 'check'),
        ly.lex.lilypond.Markup: data.textFormat('lilypond', 'markup'),
        ly.lex.lilypond.LyricMode: data.textFormat('lilypond', 'lyricmode'),
        ly.lex.lilypond.Lyric: data.textFormat('lilypond', 'lyrictext'),
        ly.lex.lilypond.Repeat: data.textFormat('lilypond', 'repeat'),
        ly.lex.lilypond.Specifier: data.textFormat('lilypond', 'specifier'),
        ly.lex.lilypond.UserCommand: data.textFormat('lilypond', 'usercommand'),
        ly.lex.lilypond.Delimiter: data.textFormat('lilypond', 'delimiter'),
        ly.lex.lilypond.ContextName: data.textFormat('lilypond', 'context'),
        ly.lex.lilypond.GrobName: data.textFormat('lilypond', 'grob'),
        ly.lex.lilypond.ContextProperty: data.textFormat('lilypond', 'property'),
        ly.lex.lilypond.Variable: data.textFormat('lilypond', 'variable'),
        ly.lex.lilypond.UserVariable: data.textFormat('lilypond', 'uservariable'),
        ly.lex.lilypond.Value: data.textFormat('lilypond', 'value'),
        ly.lex.lilypond.String: data.textFormat('lilypond', 'string'),
        ly.lex.lilypond.StringQuoteEscape: data.textFormat('lilypond', 'stringescape'),
        ly.lex.lilypond.Comment: data.textFormat('lilypond', 'comment'),
        ly.lex.lilypond.Error: data.textFormat('lilypond', 'error'),
        ly.lex.lilypond.Repeat: data.textFormat('lilypond', 'repeat'),
        ly.lex.lilypond.Tremolo: data.textFormat('lilypond', 'repeat'),
        

        # Scheme
        ly.lex.lilypond.SchemeStart: data.textFormat('scheme', 'scheme'),
        ly.lex.scheme.Scheme: data.textFormat('scheme', 'scheme'),
        ly.lex.scheme.String: data.textFormat('scheme', 'string'),
        ly.lex.scheme.Comment: data.textFormat('scheme', 'comment'),
        ly.lex.scheme.Number: data.textFormat('scheme', 'number'),
        ly.lex.scheme.LilyPond: data.textFormat('scheme', 'lilypond'),
        ly.lex.scheme.Keyword: data.textFormat('scheme', 'keyword'),
        ly.lex.scheme.Function: data.textFormat('scheme', 'function'),
        ly.lex.scheme.Variable: data.textFormat('scheme', 'variable'),
        ly.lex.scheme.Constant: data.textFormat('scheme', 'constant'),
        ly.lex.scheme.OpenParen: data.textFormat('scheme', 'delimiter'),
        ly.lex.scheme.CloseParen: data.textFormat('scheme', 'delimiter'),
        
        # HTML
        ly.lex.html.Tag: data.textFormat('html', 'tag'),
        ly.lex.html.AttrName: data.textFormat('html', 'attribute'),
        ly.lex.html.Value: data.textFormat('html', 'value'),
        ly.lex.html.String: data.textFormat('html', 'string'),
        ly.lex.html.EntityRef: data.textFormat('html', 'entityref'),
        ly.lex.html.Comment: data.textFormat('html', 'comment'),
        ly.lex.html.LilyPondTag: data.textFormat('html', 'lilypondtag'),
        
        # Texinfo
        ly.lex.texinfo.Keyword: data.textFormat('texinfo', 'keyword'),
        ly.lex.texinfo.Block: data.textFormat('texinfo', 'block'),
        ly.lex.texinfo.Attribute: data.textFormat('texinfo', 'attribute'),
        ly.lex.texinfo.EscapeChar: data.textFormat('texinfo', 'escapechar'),
        ly.lex.texinfo.Verbatim: data.textFormat('texinfo', 'verbatim'),
        ly.lex.texinfo.Comment: data.textFormat('texinfo', 'comment'),
        
        
    } # end of mapping dict


def highlighter(document):
    """Return the Highlighter for this document."""
    return Highlighter.instance(document)


def highlightFormats():
    """Return the global HighlightFormats instance."""
    global _highlightFormats
    try:
        return _highlightFormats
    except NameError:
        _highlightFormats = HighlightFormats(textformats.formatData('editor'))
        return _highlightFormats


def _resetHighlightFormats():
    """Remove the global HighlightFormats instance, so it's recreated next time."""
    global _highlightFormats
    try:
        del _highlightFormats
    except NameError:
        pass

app.settingsChanged.connect(_resetHighlightFormats, -100) # before all others


# when highlighting, don't test all the Token base classes
_token_mro_slice = slice(1, -len(ly.lex.Token.__mro__))


class HighlightFormats(object):
    """Manages a dictionary with all highlightformats coupled to token types."""
    def __init__(self, data):
        """Initialize ourselves with a TextFormatData instance."""
        self._formats = mapping(data)
    
    def format(self, token):
        """Return the format defined in the formats dictionary for the token class.
        
        Returns None if no format is defined.
        Returned values are cached to improve the lookup speed.
        
        """
        d = self._formats
        cls = token.__class__
        try:
            return d[cls]
        except KeyError:
            for c in cls.__mro__[_token_mro_slice]:
                try:
                    f = d[c]
                    break
                except KeyError:
                    pass
            else:
                f = None
            d[cls] = f
            return f

        
class Highlighter(QSyntaxHighlighter, plugin.Plugin):
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
            formats = highlightFormats()
            for token in tokens:
                f = formats.format(token)
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
        """Return a thawn ly.lex.State() object at the *end* of the QTextBlock.
        
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


def htmlCopy(document, type='editor'):
    """Return a new QTextDocument with highlighting set as HTML textcharformats."""
    data = textformats.formatData(type)
    doc = QTextDocument()
    doc.setDefaultFont(data.font)
    doc.setPlainText(document.toPlainText())
    if metainfo.info(document).highlighting:
        highlight(doc, HighlightFormats(data), ly.lex.state(documentinfo.mode(document)))
    return doc


def highlight(document, formats=None, state=None):
    """Highlight a generic QTextDocument once.
    
    formats is an optional HighlightFormats instance, defaulting to the current
    configured editor highlighting formats.
    state is an optional ly.lex.State instance. By default the text type
    is guessed.
    
    """
    if formats is None:
        formats = highlightFormats()
    if state is None:
        state = ly.lex.guessState(document.toPlainText())
    cursor = QTextCursor(document)
    block = document.firstBlock()
    while block.isValid():
        for token in state.tokens(block.text()):
            f = formats.format(token)
            if f:
                cursor.setPosition(block.position() + token.pos)
                cursor.setPosition(block.position() + token.end, QTextCursor.KeepAnchor)
                cursor.setCharFormat(f)
        block = block.next()


