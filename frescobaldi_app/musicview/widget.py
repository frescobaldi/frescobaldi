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
The PDF preview panel widget.
"""



import collections
import itertools
import os
import weakref

from PyQt5.QtCore import pyqtSignal, QMargins, QPoint, QRect, Qt, QUrl
from PyQt5.QtGui import QCursor, QTextCharFormat
from PyQt5.QtWidgets import QToolTip, QVBoxLayout, QWidget

try:
    import popplerqt5
except ImportError:
    pass

import qpageview
import qpageview.layout
import qpageview.highlight
import qpageview.rubberband
import pagedview

import app
import icons
import helpers
import textedit
import textformats
import lydocument
import viewhighlighter
import ly.lex.lilypond

from . import pointandclick


class MusicView(QWidget):
    """Widget containing the qpopplerview.View."""
    def __init__(self, dockwidget):
        """Creates the Music View for the dockwidget."""
        super(MusicView, self).__init__(dockwidget)

        self._positions = weakref.WeakKeyDictionary()
        self._currentDocument = None
        self._links = None
        self._clicking_link = False

        self._highlightFormat = QTextCharFormat()
        self._highlightMusicFormat = qpageview.highlight.Highlighter()
        self._highlightRange = None

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.view = pagedview.View(self)
        self.view.setRubberband(qpageview.rubberband.Rubberband())
        layout.addWidget(self.view)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        self.view.setViewMode(qpageview.FitWidth)
        self.view.setPageLayout(qpageview.layout.RowPageLayout())
        self.view.setLinkHighlighter(qpageview.highlight.Highlighter())
        self.view.linkClicked.connect(self.slotLinkClicked)
        self.view.linkHovered.connect(self.slotLinkHovered)
        self.view.linkLeft.connect(self.slotLinkLeft)
        #self.view.setShowUrlTips(False)
        self.view.linkHelpRequested.connect(self.slotLinkHelpRequested)

        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.showContextMenu)

        # react if cursor of current text document moves
        dockwidget.mainwindow().currentViewChanged.connect(self.slotCurrentViewChanged)
        view = dockwidget.mainwindow().currentView()
        if view:
            self.slotCurrentViewChanged(view)

    def sizeHint(self):
        """Returns the initial size the PDF (Music) View prefers."""
        return self.parent().mainwindow().size() / 2

    def openDocument(self, doc):
        """Opens a documents.Document instance."""
        self.clear()
        self._currentDocument = doc
        document = doc.document()
        if document:
            self._links = pointandclick.links(document)
            self.view.loadPdf(document)
            position = self._positions.get(doc)
            if position:
                self.view.setPosition(position, allowKinetic=False)

    def clear(self):
        """Empties the view."""
        cur = self._currentDocument
        if cur:
            self._positions[cur] = self.view.position()
        self._currentDocument = None
        self._links = None
        self._highlightRange = None
        self.view.clear()

    def readSettings(self):
        """Reads the settings from the user's preferences."""
        # background and highlight colors of music view
        colors = textformats.formatData('editor').baseColors
        self._highlightMusicFormat.color = colors['musichighlight']
        color = colors['selectionbackground']
        color.setAlpha(128)
        self._highlightFormat.setBackground(color)

    def slotLinkClicked(self, ev, page, link):
        """Called when the use clicks a link.

        If the links is a textedit link, opens the document and puts the cursor there.
        Otherwise, call the helpers module to open the destination.

        """
        if ev.button() == Qt.RightButton:
            return
        cursor = self._links.cursor(link, True)
        if cursor:
            if ev.modifiers() & Qt.ShiftModifier:
                import editinplace
                editinplace.edit(self, cursor, ev.globalPos())
            else:
                import browseriface
                mainwindow = self.parent().mainwindow()
                self._clicking_link = True
                browseriface.get(mainwindow).setTextCursor(cursor, findOpenView=True)
                self._clicking_link = False
                import widgets.blink
                widgets.blink.Blinker.blink_cursor(mainwindow.currentView())
                mainwindow.activateWindow()
                mainwindow.currentView().setFocus()
        elif link.url and not link.url.startswith('textedit:'):
            helpers.openUrl(QUrl(link.url))
        elif (hasattr(link, "linkobj") and isinstance(link.linkobj, popplerqt5.Poppler.LinkGoto)
              and not link.linkobj.isExternal()):
            self.view.setCurrentPageNumber(link.linkobj.destination().pageNumber())

    def slotLinkHovered(self, page, link):
        """Called when the mouse hovers a link.

        If the links points to the current editor document, the token(s) it points
        at are highlighted using a transparent selection color.

        The highlight shows for a few seconds but disappears when the mouse moves
        off the link or when the link is clicked.

        """
        cursor = self._links.cursor(link)
        if not cursor or cursor.document() != self.parent().mainwindow().currentDocument():
            return

        # highlight token(s) at this cursor
        cursors = pointandclick.positions(cursor)
        if cursors:
            view = self.parent().mainwindow().currentView()
            viewhighlighter.highlighter(view).highlight(self._highlightFormat, cursors, 2, 5000)

    def slotLinkLeft(self):
        """Called when the mouse moves off a previously highlighted link."""
        view = self.parent().mainwindow().currentView()
        viewhighlighter.highlighter(view).clear(self._highlightFormat)

    def slotLinkHelpRequested(self, ev, page, link):
        """Called when a ToolTip wants to appear above the hovered link."""
        pos = self.view.viewport().mapToGlobal(ev.pos())
        if link.url:
            cursor = self._links.cursor(link)
            if cursor:
                import documenttooltip
                text = documenttooltip.text(cursor)
            else:
                l = textedit.link(link.url)
                if l:
                    text = "{0} ({1}:{2})".format(os.path.basename(l.filename), l.line, l.column)
                else:
                    text = link.url
        elif hasattr(link, "linkobj") and isinstance(link.linkobj, popplerqt5.Poppler.LinkGoto):
            text = _("Page {num}").format(num=link.linkobj.destination().pageNumber())
            if link.linkobj.isExternal():
                text = link.linkobj.fileName() + "\n" + text
        else:
            return
        QToolTip.showText(pos, text, self.view, page.linkRect(link))

    def slotCurrentViewChanged(self, view, old=None):
        self.view.clearHighlight(self._highlightMusicFormat)
        if old:
            old.cursorPositionChanged.disconnect(self.slotCursorPositionChanged)
        view.cursorPositionChanged.connect(self.slotCursorPositionChanged)

    def slotCursorPositionChanged(self):
        """Called when the user moves the text cursor."""
        if not self.isVisible() or not self._links:
            return # not visible of no PDF in the viewer

        view = self.parent().mainwindow().currentView()
        links = self._links.boundLinks(view.document())
        if not links:
            return # the PDF contains no references to the current text document

        s = links.indices(view.textCursor())
        if s is False:
            self.clearHighlighting()
        elif s:
            # move if sync is enabled and the cursor did not move as a result of
            # clicking a link
            if (not self._clicking_link
                and self.parent().actionCollection.music_sync_cursor.isChecked()):
                rect = self.destinationsRect(links.destinations()[s])
                self.view.ensureVisible(rect, QMargins(20, 20, 20, 20))

            # perform highlighting after move has been started. This is to ensure that if kinetic scrolling is
            # is enabled its speed is already set so that we can adjust the highlight timer.
            self.highlight(links.destinations(), s)

    def highlight(self, destinations, slice, msec=None):
        """(Internal) Highlights the from the specified destinations the specified slice."""
        count = slice.stop - slice.start
        if self._highlightRange == slice and self.view.isHighlighting(self._highlightMusicFormat):
            return # don't redraw if same
        self._highlightRange = slice
        layout = self.view.pageLayout()
        areas = collections.defaultdict(list)
        for dest in destinations[slice]:
            for pageNum, rect in dest:
                areas[layout[pageNum]].append(rect)
        if msec is None:
            msec = 5000 if count > 1 else 2000 # show selections longer
        # RC: increased timer to give some time to the kinetic scrolling to complete.
        if self.view.isScrolling():
            msec += self.view.remainingScrollTime()
        self.view.highlight(self._highlightMusicFormat, areas, msec)

    def clearHighlighting(self):
        """Clear the highlighted areas."""
        self._highlightRange = None
        self.view.clearHighlight(self._highlightMusicFormat)

    def showCurrentLinks(self):
        """Scrolls the view if necessary to show objects at current text cursor."""
        if not self._links:
            return # no PDF in viewer

        view = self.parent().mainwindow().currentView()
        links = self._links.boundLinks(view.document())
        if not links:
            return # the PDF contains no references to the current text document

        s = links.indices(view.textCursor())
        if not s:
            return
        rect = self.destinationsRect(links.destinations()[s])
        self.view.ensureVisible(rect, QMargins(20, 20, 20, 20))
        self.highlight(links.destinations(), s, 10000)

    def destinationsRect(self, destinations):
        """Return the rectangle containing all destinations."""
        layout = self.view.pageLayout()
        rect = QRect()
        for dest in destinations:
            for pageNum, r in dest:
                page = layout[pageNum]
                rect = rect.united(page.mapToPage(1, 1).rect(r).translated(page.pos()))
        # not larger than viewport
        rect.setSize(rect.size().boundedTo(self.view.viewport().size()))
        return rect

    def showContextMenu(self):
        """Called when the user right-clicks or presses the context menu key."""
        pos = self.view.mapToGlobal(QPoint(0, 0))
        link, cursor = None, None
        # mouse inside view?
        if self.view.mapFromGlobal(QCursor.pos()) in self.view.viewport().rect():
            pos = QCursor.pos()
            pos_in_viewport = self.view.viewport().mapFromGlobal(pos)
            page, link = self.view.linkAt(pos_in_viewport)
            if link:
                cursor = self._links.cursor(link, True)
        from . import contextmenu
        contextmenu.show(pos, self.parent(), link, cursor)

