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


_highlightFormats = None

def highlightFormats():
    global _highlightFormats
    if _highlightFormats is None:
        _highlightFormats = makeHighlightFormats()
    return _highlightFormats
    
def _resetHighlightFormats():
    global _highlightFormats
    _highlightFormats = None

app.settingsChanged.connect(_resetHighlightFormats, -100) # before all others


def makeHighlightFormats():
    """Returns a dictionary with all highlightformats coupled to token types."""
    d = {}
    data = textformats.textFormatData()
    
    # LilyPond
    d[ly.tokenize.lilypond.Comment] = data.textFormat('lilypond', 'comment')
    d[ly.tokenize.lilypond.String] = data.textFormat('lilypond', 'string')
    
    # HTML
    d[ly.tokenize.html.TagStart] = data.textFormat('html', 'tag')
    d[ly.tokenize.html.TagEnd] = d[ly.tokenize.html.TagStart]
    d[ly.tokenize.html.AttrName] = data.textFormat('html', 'attribute')
    d[ly.tokenize.html.String] = data.textFormat('html', 'string')
    d[ly.tokenize.html.EntityRef] = data.textFormat('html', 'entityref')
    d[ly.tokenize.html.Comment] = data.textFormat('html', 'comment')
    
    
    return d
    
        


class Highlighter(QSyntaxHighlighter):
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        self.setDocument(document)
        self._states = []
        app.settingsChanged.connect(self.rehighlight)
        
    def highlightBlock(self, text):
        prev = self.previousBlockState()
        if 0 <= prev < len(self._states):
            state = ly.tokenize.State.thaw(self._states[prev])
        else:
            state = ly.tokenize.State(text)
        
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
                
        cur = state.freeze()
        try:
            self.setCurrentBlockState(self._states.index(cur))
        except ValueError:
            self.setCurrentBlockState(len(self._states))
            self._states.append(cur)

