# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
The PDF preview panel widget.
"""

from __future__ import unicode_literals

import itertools
import os
import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4
import qpopplerview

import app
import icons
import textformats
import tokeniter
import ly.tokenize.lilypond

from . import pointandclick


class MusicView(QWidget):
    def __init__(self, dockwidget):
        """Creates the Music View for the dockwidget."""
        super(MusicView, self).__init__(dockwidget)
        
        self._positions = weakref.WeakKeyDictionary()
        self._currentDocument = lambda: None
        
        self._highlightFormat = QTextCharFormat()
        self._highlightMusicFormat = qpopplerview.Highlighter()
        self._highlightRange = None
        self._highlightTimer = QTimer(singleShot=True, interval= 250, timeout=self.updateHighlighting)
        self._highlightRemoveTimer = QTimer(singleShot=True, timeout=self.clearHighlighting)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.view = qpopplerview.View(self)
        layout.addWidget(self.view)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        self.view.setViewMode(qpopplerview.FitWidth)
        self.view.surface().pageLayout().setDPI(self.physicalDpiX(), self.physicalDpiY())
        self.view.viewModeChanged.connect(self.slotViewModeChanged)
        self.view.surface().linkClicked.connect(self.slotLinkClicked)
        self.view.surface().linkHovered.connect(self.slotLinkHovered)
        self.view.surface().linkLeft.connect(self.slotLinkLeft)
        self.view.surface().setShowUrlTips(False)
        self.view.surface().linkHelpRequested.connect(self.slotLinkHelpRequested)
        self.slotViewModeChanged(self.view.viewMode())
        
        zoomer = self.parent().actionCollection.music_zoom_combo
        self.view.viewModeChanged.connect(zoomer.updateZoomInfo)
        self.view.surface().pageLayout().scaleChanged.connect(zoomer.updateZoomInfo)
        
        # react if cursor of current text document moves
        dockwidget.mainwindow().currentViewChanged.connect(self.slotCurrentViewChanged)
        view = dockwidget.mainwindow().currentView()
        if view:
            self.slotCurrentViewChanged(view)

    def sizeHint(self):
        """Returns the initial size the PDF (Music) View prefers."""
        return self.parent().mainwindow().size() / 2
        
    def slotViewModeChanged(self, viewmode):
        """Called when the view mode of the view changes."""
        ac = self.parent().actionCollection
        ac.music_fit_width.setChecked(viewmode == qpopplerview.FitWidth)
        ac.music_fit_height.setChecked(viewmode == qpopplerview.FitHeight)
        ac.music_fit_both.setChecked(viewmode == qpopplerview.FitBoth)

    def openDocument(self, doc):
        """Opens a documents.Document instance."""
        cur = self._currentDocument()
        if cur:
            self._positions[cur] = self.view.position()
            
        self._currentDocument = weakref.ref(doc)
        self._links = pointandclick.links(doc.document())
        self.view.load(doc.document())
        position = self._positions.get(doc, (0, 0, 0))
        self.view.setPosition(position)
        self._highlightRange = None
        self._highlightTimer.stop()

    def clear(self):
        """Empties the view."""
        cur = self._currentDocument()
        if cur:
            self._positions[cur] = self.view.position()
        self._currentDocument = lambda: None
        self.view.clear()
        
    def readSettings(self):
        """Reads the settings from the user's preferences."""
        color = textformats.formatData('editor').baseColors['selectionbackground']
        color.setAlpha(128)
        self._highlightFormat.setBackground(color)
        qpopplerview.cache.options().setPaperColor(textformats.formatData('editor').baseColors['paper'])
        self.view.redraw()

    def slotLinkClicked(self, ev, page, link):
        """Called when the use clicks a link.
        
        If the links is a textedit link, opens the document and puts the cursor there.
        Otherwise, call the QDesktopServices to open the destination.
        
        """
        cursor = self._links.cursor(link, True)
        if cursor:
            self.parent().mainwindow().setTextCursor(cursor, findOpenView=True)
            self.slotLinkLeft() # hide possible highlighting
        elif ev.button() != Qt.RightButton and isinstance(link, popplerqt4.Poppler.LinkBrowse):
            QDesktopServices.openUrl(QUrl(link.url()))

    def slotLinkHovered(self, page, link):
        """Called when the mouse hovers a link.
        
        If the links points to the current editor document, the token(s) it points
        at are highlighted using a transparent selection color.
        
        The highlight shows for a few seconds but disappears when the mouse moves
        off the link or when the link is clicked.
        
        """
        self.view.surface().highlight(self._highlightMusicFormat, [(page, link.linkArea().normalized())], 2000)
        cursor = self._links.cursor(link)
        if not cursor or cursor.document() != self.parent().mainwindow().currentDocument():
            return
        
        # highlight token(s) at this cursor
        document = cursor.document()
        block = cursor.block()
        column = cursor.position() - block.position()
        tokens = tokeniter.TokenIterator(block)
        source, state = tokens.forward_state()
        # go to our column
        for token in source:
            if token.pos >= column or tokens.block != block:
                break
        else:
            return
        
        start = token.pos + block.position()
        cur = QTextCursor(document)
        cur.setPosition(start)
        cursors = [cur]
        
        # some heuristic to find the relevant range(s) the linked grob represents
        if isinstance(token, ly.tokenize.lilypond.Direction):
            # a _, - or ^ is found; find the next token
            for token in source:
                if not isinstance(token, (ly.tokenize.Space, ly.tokenize.Comment)):
                    break
        end = token.end + block.position()
        if token == '\\markup':
            # find the end of the markup expression
            depth = len(state)
            for token in source:
                if len(state) < depth:
                    end = token.end + tokens.block.position()
                    break
        elif token == '"':
            # find the end of the string
            for token in source:
                if isinstance(token, ly.tokenize.StringEnd):
                    end = token.end + tokens.block.position()
                    break
        elif isinstance(token, ly.tokenize.MatchStart):
            # find the end of slur, beam. ligature, phrasing slur, etc.
            name = token.matchname
            nest = 1
            for token in source:
                if isinstance(token, ly.tokenize.MatchEnd) and token.matchname == name:
                    nest -= 1
                    if nest == 0:
                        cur2 = QTextCursor(document)
                        cur2.setPosition(token.pos + tokens.block.position())
                        cur2.setPosition(token.end + tokens.block.position(), QTextCursor.KeepAnchor)
                        cursors.append(cur2)
                        break
                elif isinstance(token, ly.tokenize.MatchStart) and token.matchname == name:
                    nest += 1
                    
        cur.setPosition(end, QTextCursor.KeepAnchor)
        
        view = self.parent().mainwindow().currentView()
        view.highlight(self._highlightFormat, cursors, 2, 5000)
    
    def slotLinkLeft(self):
        """Called when the mouse moves off a previously highlighted link."""
        self.view.surface().clearHighlight(self._highlightMusicFormat)
        view = self.parent().mainwindow().currentView()
        view.clearHighlight(self._highlightFormat)

    def slotLinkHelpRequested(self, pos, page, link):
        """Called when a ToolTip wants to appear above the hovered link."""
        if isinstance(link, popplerqt4.Poppler.LinkBrowse):
            text = link.url()
            cursor = self._links.cursor(link)
            m = pointandclick.textedit_match(link.url())
            if m:
                filename, line, column = pointandclick.readurl(m)
                text = "{0}  {1}:{2}".format(os.path.basename(filename), line, column)
            QToolTip.showText(pos, text, self.view.surface(), page.linkRect(link.linkArea()))

    def slotCurrentViewChanged(self, view, old):
        self.view.surface().clearHighlight(self._highlightMusicFormat)
        if old:
            old.cursorPositionChanged.disconnect(self.slotCursorPositionChanged)
        view.cursorPositionChanged.connect(self.slotCursorPositionChanged)
    
    def slotCursorPositionChanged(self):
        """Called when the user moves the text cursor."""
        if not self.isVisible() or not self._currentDocument():
            return # not visible of no PDF in the viewer
        
        view = self.parent().mainwindow().currentView()
        links = self._links.boundLinks(view.document())
        if not links:
            return # the PDF contains no references to the current text document
        
        cursors = links.cursors()
        
        def findlink(pos):
            # binary search in list of cursors
            lo, hi = 0, len(cursors)
            while lo < hi:
                mid = (lo + hi) // 2
                if pos < cursors[mid].position():
                    hi = mid
                else:
                    lo = mid + 1
            return lo - 1
        
        cursor = view.textCursor()
        if cursor.hasSelection():
            end = findlink(cursor.selectionEnd() - 1)
            if end >= 0:
                start = findlink(cursor.selectionStart())
                if start < 0 or cursors[start].position() < cursor.selectionStart():
                    start += 1
                if start <= end:
                    self.highlight(links, start, end, 5000)
                    return
            self.clearHighlighting()
            return
            
        index = findlink(cursor.position())
        if index < 0:
            return # before all other links
        
        cur2 = cursors[index]
        if cur2.position() < cursor.position():
            # is the cursor at an ending token like a slur end?
            prevcol = -1
            if cur2.block() == cursor.block():
                prevcol = cur2.position() - cur2.block().position()
            col = cursor.position() - cursor.block().position()
            found = False
            tokens = tokeniter.TokenIterator(cursor.block(), True)
            for token in tokens.backward(False):
                if token.pos <= col and token.pos > prevcol:
                    if isinstance(token, ly.tokenize.MatchEnd) and token.matchname in (
                            'slur', 'phrasingslur', 'beam'):
                        # YES! now go backwards to find the opening token
                        nest = 1
                        name = token.matchname
                        for token in tokens.backward():
                            if isinstance(token, ly.tokenize.MatchStart) and token.matchname == name:
                                nest -= 1
                                if nest == 0:
                                    found = True
                                    break
                            elif isinstance(token, ly.tokenize.MatchEnd) and token.matchname == name:
                                nest += 1
                        break
            if found:
                index = findlink(tokens.cursor().position())
                if index < 0:
                    return
            elif cur2.block() != cursor.block():
                self.clearHighlighting() # not on same line
                return
        # highlight it!
        self.highlight(links, index, index, 2000)

    def highlight(self, links, start, end, msec):
        """(Internal) Highlights the links in links.destinations()[start : end + 1] for msec seconds."""
        self._destinations = links.destinations()
        self._highlightRemoveTimer.start(msec)
        if self._highlightRange == (start, end):
            return # don't rewrite if same
        self._highlightRange = (start, end)
        if end - start > 100:
            self._highlightTimer.start()
        else:
            self._highlightTimer.stop()
            self.updateHighlighting()
    
    def updateHighlighting(self):
        """Really orders the view's surface to draw the highlighting."""
        layout = self.view.surface().pageLayout()
        start, end = self._highlightRange
        areas = [(layout[pageNum], rect)
                    for dest in self._destinations[start:end+1]
                    for pageNum, rect in dest]
        self.view.surface().highlight(self._highlightMusicFormat, areas)
    
    def clearHighlighting(self):
        """Called on timeout of the _highlightRemoveTimer."""
        self._highlightRange = None
        self.view.surface().clearHighlight(self._highlightMusicFormat)


