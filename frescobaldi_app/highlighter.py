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


from PyQt4.QtCore import *
from PyQt4.QtGui import *


import ly.tokenize
import app
import textformats
import metainfo


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
    d[ly.tokenize.lilypond.Markup] = data.textFormat('lilypond', 'markup')
    d[ly.tokenize.lilypond.UserCommand] = data.textFormat('lilypond', 'usercommand')
    d[ly.tokenize.lilypond.Delimiter] = data.textFormat('lilypond', 'delimiter')
    d[ly.tokenize.lilypond.Context] = data.textFormat('lilypond', 'context')
    d[ly.tokenize.lilypond.Grob] = data.textFormat('lilypond', 'grob')
    d[ly.tokenize.lilypond.StringQuoteEscape] = data.textFormat('lilypond', 'stringescape')
    d[ly.tokenize.lilypond.String] = data.textFormat('lilypond', 'string')
    d[ly.tokenize.lilypond.Comment] = data.textFormat('lilypond', 'comment')
    
    
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
    d[ly.tokenize.texi.Keyword] = data.textFormat('texi', 'keyword')
    d[ly.tokenize.texi.Block] = data.textFormat('texi', 'block')
    d[ly.tokenize.texi.Attribute] = data.textFormat('texi', 'attribute')
    d[ly.tokenize.texi.EscapeChar] = data.textFormat('texi', 'escapechar')
    d[ly.tokenize.texi.Verbatim] = data.textFormat('texi', 'verbatim')
    d[ly.tokenize.texi.Comment] = data.textFormat('texi', 'comment')
    
    
    return d
    
        


class Highlighter(QSyntaxHighlighter):
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        self.setDocument(document)
        self._states = []
        app.settingsChanged.connect(self.rehighlight)
        self._highlighting = metainfo.info(document).highlighting
        document.loaded.connect(self._resetHighlighting)
        
    def _resetHighlighting(self):
        self.setHighlighting(metainfo.info(self.document()).highlighting)
        
    def highlightBlock(self, text):
        prev = self.previousBlockState()
        if 0 <= prev < len(self._states):
            state = ly.tokenize.State.thaw(self._states[prev])
        elif not text or text.isspace():
            self.setCurrentBlockState(prev - 1) # keep the highligher coming back
            return
        else:
            state = ly.tokenize.State(ly.tokenize.guessState(self.document().toPlainText()))
        
        if self._highlighting:
            setFormat = lambda f: self.setFormat(token.pos, len(token), f)
            formats = highlightFormats()
            for token in ly.tokenize.tokens(text, state):
                for cls in token.__class__.__mro__:
                    if cls is not ly.tokenize.Token:
                        try:
                            setFormat(formats[cls])
                        except KeyError:
                            continue
                    break
        else:
            for token in ly.tokenize.tokens(text, state):
                pass
        
        cur = state.freeze()
        try:
            self.setCurrentBlockState(self._states.index(cur))
        except ValueError:
            self.setCurrentBlockState(len(self._states))
            self._states.append(cur)

    def setHighlighting(self, enable):
        """Enables or disables highlighting."""
        changed = enable != self._highlighting
        self._highlighting = enable
        if changed:
            metainfo.info(self.document()).highlighting = enable
            self.rehighlight()
            
    def isHighlighting(self):
        """Returns whether highlighting is active."""
        return self._highlighting
        
    def state(self, block):
        """Returns a thawn ly.tokenize.State() object at the beginning of the given QTextBlock.
        
        This assumes the highligher has already run through the whole document.
        
        """
        userState = block.previous().userState()
        if 0 <= userState < len(self._states):
            return ly.tokenize.State.thaw(self._states[userState])
        return ly.tokenize.State(ly.tokenize.guessState(self.document().toPlainText()))


def htmlCopy(document, data):
    """Returns a new QTextDocument with highlighting set as HTML textcharformats."""
    formats = makeHighlightFormats(data)
    
    doc = QTextDocument()
    doc.setDefaultFont(data.font)
    text = document.toPlainText()
    doc.setPlainText(text)
    cursor = QTextCursor(doc)
    state = ly.tokenize.State(ly.tokenize.guessState(text))
    for token in ly.tokenize.tokens(text, state):
        for cls in token.__class__.__mro__:
            if cls is not ly.tokenize.Token:
                try:
                    f = formats[cls]
                except KeyError:
                    continue
                cursor.setPosition(token.pos)
                cursor.setPosition(token.pos + len(token), QTextCursor.KeepAnchor)
                cursor.setCharFormat(f)
            break
    return doc
    
