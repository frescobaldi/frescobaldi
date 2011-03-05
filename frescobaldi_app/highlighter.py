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
The Highlighter class provides syntax highlighting and more information
about a document's contents.
"""


from PyQt4.QtGui import (
    QSyntaxHighlighter, QTextBlockUserData, QTextCursor, QTextDocument)


import ly.tokenize
import ly.tokenize.lilypond
import ly.tokenize.scheme
import ly.tokenize.html
import ly.tokenize.texinfo

import app
import textformats
import metainfo
import variables
import documentinfo


metainfo.define('highlighting', True)


# when highlighting, don't test all the Token base classes
_token_mro_slice = slice(0, -len(ly.tokenize.Token.__mro__))


_highlightFormats = None

def highlightFormats():
    global _highlightFormats
    if _highlightFormats is None:
        _highlightFormats = makeHighlightFormats(textformats.formatData('editor'))
    return _highlightFormats
    
def _resetHighlightFormats():
    global _highlightFormats
    _highlightFormats = None

app.settingsChanged.connect(_resetHighlightFormats, -100) # before all others


def makeHighlightFormats(data):
    """Returns a dictionary with all highlightformats coupled to token types."""
    d = {}
    
    # LilyPond
    d[ly.tokenize.lilypond.Keyword] = data.textFormat('lilypond', 'keyword')
    d[ly.tokenize.lilypond.Command] = data.textFormat('lilypond', 'command')
    d[ly.tokenize.lilypond.Dynamic] = data.textFormat('lilypond', 'dynamic')
    d[ly.tokenize.lilypond.Note] = data.textFormat('lilypond', 'pitch')
    d[ly.tokenize.lilypond.Rest] = data.textFormat('lilypond', 'pitch')
    d[ly.tokenize.lilypond.Skip] = data.textFormat('lilypond', 'pitch')
    d[ly.tokenize.lilypond.Duration] = data.textFormat('lilypond', 'duration')
    d[ly.tokenize.lilypond.Articulation] = data.textFormat('lilypond', 'articulation')
    d[ly.tokenize.lilypond.Slur] = data.textFormat('lilypond', 'slur')
    d[ly.tokenize.lilypond.Chord] = data.textFormat('lilypond', 'chord')
    d[ly.tokenize.lilypond.Markup] = data.textFormat('lilypond', 'markup')
    d[ly.tokenize.lilypond.LyricMode] = data.textFormat('lilypond', 'lyricmode')
    d[ly.tokenize.lilypond.Lyric] = data.textFormat('lilypond', 'lyrictext')
    d[ly.tokenize.lilypond.LyricTie] = data.textFormat('lilypond', 'slur')
    d[ly.tokenize.lilypond.Repeat] = data.textFormat('lilypond', 'repeat')
    d[ly.tokenize.lilypond.Specifier] = data.textFormat('lilypond', 'specifier')
    d[ly.tokenize.lilypond.UserCommand] = data.textFormat('lilypond', 'usercommand')
    d[ly.tokenize.lilypond.Delimiter] = data.textFormat('lilypond', 'delimiter')
    d[ly.tokenize.lilypond.ContextName] = data.textFormat('lilypond', 'context')
    d[ly.tokenize.lilypond.GrobName] = data.textFormat('lilypond', 'grob')
    d[ly.tokenize.lilypond.ContextProperty] = data.textFormat('lilypond', 'property')
    d[ly.tokenize.lilypond.Variable] = data.textFormat('lilypond', 'variable')
    d[ly.tokenize.lilypond.UserVariable] = data.textFormat('lilypond', 'uservariable')
    d[ly.tokenize.lilypond.Value] = data.textFormat('lilypond', 'value')
    d[ly.tokenize.lilypond.String] = data.textFormat('lilypond', 'string')
    d[ly.tokenize.lilypond.StringQuoteEscape] = data.textFormat('lilypond', 'stringescape')
    d[ly.tokenize.lilypond.Comment] = data.textFormat('lilypond', 'comment')
    d[ly.tokenize.lilypond.Error] = data.textFormat('lilypond', 'error')
    d[ly.tokenize.lilypond.Repeat] = data.textFormat('lilypond', 'repeat')
    

    # Scheme
    d[ly.tokenize.lilypond.SchemeStart] = data.textFormat('scheme', 'scheme')
    d[ly.tokenize.scheme.Scheme] = d[ly.tokenize.lilypond.SchemeStart]
    d[ly.tokenize.scheme.String] = data.textFormat('scheme', 'string')
    d[ly.tokenize.scheme.Comment] = data.textFormat('scheme', 'comment')
    d[ly.tokenize.scheme.Number] = data.textFormat('scheme', 'number')
    d[ly.tokenize.scheme.LilyPond] = data.textFormat('scheme', 'lilypond')
    
    # HTML
    d[ly.tokenize.html.Tag] = data.textFormat('html', 'tag')
    d[ly.tokenize.html.AttrName] = data.textFormat('html', 'attribute')
    d[ly.tokenize.html.Value] = data.textFormat('html', 'value')
    d[ly.tokenize.html.String] = data.textFormat('html', 'string')
    d[ly.tokenize.html.EntityRef] = data.textFormat('html', 'entityref')
    d[ly.tokenize.html.Comment] = data.textFormat('html', 'comment')
    d[ly.tokenize.html.LilyPondTag] = data.textFormat('html', 'lilypondtag')
    
    # Texinfo
    d[ly.tokenize.texinfo.Keyword] = data.textFormat('texinfo', 'keyword')
    d[ly.tokenize.texinfo.Block] = data.textFormat('texinfo', 'block')
    d[ly.tokenize.texinfo.Attribute] = data.textFormat('texinfo', 'attribute')
    d[ly.tokenize.texinfo.EscapeChar] = data.textFormat('texinfo', 'escapechar')
    d[ly.tokenize.texinfo.Verbatim] = data.textFormat('texinfo', 'verbatim')
    d[ly.tokenize.texinfo.Comment] = data.textFormat('texinfo', 'comment')
    
    
    return d
    
        
class Highlighter(QSyntaxHighlighter):
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        self.setDocument(document)
        self._states = []
        app.settingsChanged.connect(self.rehighlight)
        self._highlighting = metainfo.info(document).highlighting
        document.loaded.connect(self._resetHighlighting)
        self._mode = documentinfo.mode(document, False)
        variables.manager(document).changed.connect(self._variablesChange)
        
    def _variablesChange(self):
        mode = documentinfo.mode(self.document(), False)
        if mode != self._mode:
            self._mode = mode
            self.rehighlight()
            
    def _resetHighlighting(self):
        """Switches highlighting on or off depending on saved metainfo."""
        self.setHighlighting(metainfo.info(self.document()).highlighting)
        
    def highlightBlock(self, text):
        """Called by Qt when the highlighting of the current line needs updating."""
        # find the state of the previous line
        prev = self.previousBlockState()
        if 0 <= prev < len(self._states):
            state = ly.tokenize.thawState(self._states[prev])
        elif not text or text.isspace():
            self.setCurrentBlockState(prev - 1) # keep the highligher coming back
            return
        else:
            state = self.initialState()
        
        # collect and save the tokens
        data = userData(self.currentBlock())
        data.tokens = tokens = tuple(state.tokens(text))
        
        # save the state separately
        cur = state.freeze()
        try:
            self.setCurrentBlockState(self._states.index(cur))
        except ValueError:
            self.setCurrentBlockState(len(self._states))
            self._states.append(cur)
        
        # apply highlighting if desired
        if self._highlighting:
            setFormat = lambda f: self.setFormat(token.pos, len(token), f)
            formats = highlightFormats()
            for token in tokens:
                for cls in token.__class__.__mro__[_token_mro_slice]:
                    try:
                        setFormat(formats[cls])
                    except KeyError:
                        continue
                    break
        
    def setHighlighting(self, enable):
        """Enables or disables highlighting."""
        changed = enable != self._highlighting
        self._highlighting = enable
        if changed:
            self.rehighlight()
            
    def isHighlighting(self):
        """Returns whether highlighting is active."""
        return self._highlighting
        
    def state(self, block):
        """Returns a thawn ly.tokenize.State() object at the beginning of the given QTextBlock.
        
        This assumes the highlighter has already run through the whole document.
        To get the state info please use tokeniter.state() instead of this method.
        
        """
        userState = block.previous().userState()
        if 0 <= userState < len(self._states):
            return ly.tokenize.State.thaw(self._states[userState])
        return self.initialState()

    def initialState(self):
        """Returns the initial State for this document."""
        mode = self._mode or ly.tokenize.guessMode(self.document().toPlainText())
        return ly.tokenize.state(mode)


class BlockData(QTextBlockUserData):
    """Stores information about one text line."""
    tokens = ()


def userData(block):
    """Gets the block data for this block, setting an empty one if not yet set."""
    data = block.userData()
    if not data:
        data = BlockData()
        block.setUserData(data)
    return data


def updateTokens(block, state=None):
    """Force an update of the tokens in the given block.
    
    If state is not given, it is determined from the highlighter.
    
    """
    if state is None:
        state = block.document().highlighter.state(block)
    userData(block).tokens = tokens = tuple(state.tokens(block.text()))
    return tokens


def htmlCopy(document, data):
    """Returns a new QTextDocument with highlighting set as HTML textcharformats."""
    formats = makeHighlightFormats(data)
    
    doc = QTextDocument()
    doc.setDefaultFont(data.font)
    text = document.toPlainText()
    doc.setPlainText(text)
    state = ly.tokenize.state(documentinfo.mode(document))
    cursor = QTextCursor(doc)
    block = doc.firstBlock()
    while block.isValid():
        for token in state.tokens(block.text()):
            for cls in token.__class__.__mro__[_token_mro_slice]:
                try:
                    f = formats[cls]
                except KeyError:
                    continue
                cursor.setPosition(block.position() + token.pos)
                cursor.setPosition(block.position() + token.end, QTextCursor.KeepAnchor)
                cursor.setCharFormat(f)
                break
        block = block.next()
    return doc

