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
import textformats
import metainfo
import plugin
import variables
import documentinfo


metainfo.define('highlighting', True)


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
        self._formats = d = {}
        
        # LilyPond
        d[ly.lex.lilypond.Keyword] = data.textFormat('lilypond', 'keyword')
        d[ly.lex.lilypond.Command] = data.textFormat('lilypond', 'command')
        d[ly.lex.lilypond.Dynamic] = data.textFormat('lilypond', 'dynamic')
        d[ly.lex.lilypond.Note] = data.textFormat('lilypond', 'pitch')
        d[ly.lex.lilypond.Rest] = data.textFormat('lilypond', 'pitch')
        d[ly.lex.lilypond.Skip] = data.textFormat('lilypond', 'pitch')
        d[ly.lex.lilypond.Octave] = data.textFormat('lilypond', 'octave')
        d[ly.lex.lilypond.Duration] = data.textFormat('lilypond', 'duration')
        d[ly.lex.lilypond.OctaveCheck] = data.textFormat('lilypond', 'check')
        d[ly.lex.lilypond.Fingering] = data.textFormat('lilypond', 'fingering')
        d[ly.lex.lilypond.StringNumber] = data.textFormat('lilypond', 'stringnumber')
        d[ly.lex.lilypond.Articulation] = data.textFormat('lilypond', 'articulation')
        d[ly.lex.lilypond.Slur] = data.textFormat('lilypond', 'slur')
        d[ly.lex.lilypond.Chord] = data.textFormat('lilypond', 'chord')
        d[ly.lex.lilypond.PipeSymbol] = data.textFormat('lilypond', 'check')
        d[ly.lex.lilypond.Markup] = data.textFormat('lilypond', 'markup')
        d[ly.lex.lilypond.LyricMode] = data.textFormat('lilypond', 'lyricmode')
        d[ly.lex.lilypond.Lyric] = data.textFormat('lilypond', 'lyrictext')
        d[ly.lex.lilypond.LyricTie] = data.textFormat('lilypond', 'slur')
        d[ly.lex.lilypond.Repeat] = data.textFormat('lilypond', 'repeat')
        d[ly.lex.lilypond.Specifier] = data.textFormat('lilypond', 'specifier')
        d[ly.lex.lilypond.UserCommand] = data.textFormat('lilypond', 'usercommand')
        d[ly.lex.lilypond.Delimiter] = data.textFormat('lilypond', 'delimiter')
        d[ly.lex.lilypond.ContextName] = data.textFormat('lilypond', 'context')
        d[ly.lex.lilypond.GrobName] = data.textFormat('lilypond', 'grob')
        d[ly.lex.lilypond.ContextProperty] = data.textFormat('lilypond', 'property')
        d[ly.lex.lilypond.Variable] = data.textFormat('lilypond', 'variable')
        d[ly.lex.lilypond.UserVariable] = data.textFormat('lilypond', 'uservariable')
        d[ly.lex.lilypond.Value] = data.textFormat('lilypond', 'value')
        d[ly.lex.lilypond.String] = data.textFormat('lilypond', 'string')
        d[ly.lex.lilypond.StringQuoteEscape] = data.textFormat('lilypond', 'stringescape')
        d[ly.lex.lilypond.Comment] = data.textFormat('lilypond', 'comment')
        d[ly.lex.lilypond.Error] = data.textFormat('lilypond', 'error')
        d[ly.lex.lilypond.Repeat] = data.textFormat('lilypond', 'repeat')
        

        # Scheme
        d[ly.lex.lilypond.SchemeStart] = data.textFormat('scheme', 'scheme')
        d[ly.lex.scheme.Scheme] = d[ly.lex.lilypond.SchemeStart]
        d[ly.lex.scheme.String] = data.textFormat('scheme', 'string')
        d[ly.lex.scheme.Comment] = data.textFormat('scheme', 'comment')
        d[ly.lex.scheme.Number] = data.textFormat('scheme', 'number')
        d[ly.lex.scheme.LilyPond] = data.textFormat('scheme', 'lilypond')
        
        # HTML
        d[ly.lex.html.Tag] = data.textFormat('html', 'tag')
        d[ly.lex.html.AttrName] = data.textFormat('html', 'attribute')
        d[ly.lex.html.Value] = data.textFormat('html', 'value')
        d[ly.lex.html.String] = data.textFormat('html', 'string')
        d[ly.lex.html.EntityRef] = data.textFormat('html', 'entityref')
        d[ly.lex.html.Comment] = data.textFormat('html', 'comment')
        d[ly.lex.html.LilyPondTag] = data.textFormat('html', 'lilypondtag')
        
        # Texinfo
        d[ly.lex.texinfo.Keyword] = data.textFormat('texinfo', 'keyword')
        d[ly.lex.texinfo.Block] = data.textFormat('texinfo', 'block')
        d[ly.lex.texinfo.Attribute] = data.textFormat('texinfo', 'attribute')
        d[ly.lex.texinfo.EscapeChar] = data.textFormat('texinfo', 'escapechar')
        d[ly.lex.texinfo.Verbatim] = data.textFormat('texinfo', 'verbatim')
        d[ly.lex.texinfo.Comment] = data.textFormat('texinfo', 'comment')
    
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
        data = userData(self.currentBlock())
        data.tokens = tokens = tuple(state.tokens(text))
        
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
        """Return a thawn ly.lex.State() object at the beginning of the QTextBlock.
        
        This assumes the highlighter has already run through the whole document.
        To get the state info please use tokeniter.state() instead of this method.
        
        """
        userState = block.previous().userState()
        return self._fridge.thaw(userState) or self.initialState()

    def setInitialState(self, state):
        """Force the initial state. Use None to enable auto-detection."""
        self._initialState = self._fridge.freeze(state) if state else None
        
    def initialState(self):
        """Return the initial State for this document."""
        if self._initialState is None:
            mode = self._mode or ly.lex.guessMode(self.document().toPlainText())
            return ly.lex.state(mode)
        return self._fridge.thaw(self._initialState)


def userData(block):
    """Get the block data for this block, setting an empty one if not yet set."""
    data = block.userData()
    if not data:
        data = QTextBlockUserData()
        block.setUserData(data)
    return data


def htmlCopy(document, type='editor'):
    """Return a new QTextDocument with highlighting set as HTML textcharformats."""
    data = textformats.formatData(type)
    doc = QTextDocument()
    doc.setDefaultFont(data.font)
    doc.setPlainText(document.toPlainText())
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


