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

from __future__ import division
from __future__ import unicode_literals

import itertools
import os
import weakref

from PyQt4.QtCore import pyqtSignal, QPoint, QRect, Qt, QTimer, QUrl
from PyQt4.QtGui import (QCursor, QTextCharFormat, QToolTip, QVBoxLayout,
                         QHBoxLayout, QToolButton, QWidget)

try:
    import popplerqt4
except ImportError:
    pass

import qpopplerview
import popplerview

import app
import icons
import helpers
import textedit
import textformats
import contextmenu
import lydocument
import viewhighlighter
import ly.lex.lilypond
import userguide.util

from . import abstractviewwidget
from . import pointandclick


class AbstractPopplerWidget(abstractviewwidget.AbstractViewWidget):
    """Widget containing the qpopplerview.View."""

    # TODO: As much as possible should be moved to the base class.

    zoomChanged = pyqtSignal(int, float) # mode, scale

    def __init__(self, panel):
        """Creates the Poppler View for the panel."""
        super(AbstractPopplerWidget, self).__init__(panel)
        self.actionCollection = panel.actionCollection
        self.createProtectedFields()
        layout = self.createLayout()
        self.createHighlighters()
        self.createView()
        layout.addWidget(self.view)
        self.createHelpButton()
        self.createContextMenu()
        self.connectSlots()

    def createProtectedFields(self):
        """Create the empty protected fields that will hold actual data."""
        self._positions = weakref.WeakKeyDictionary()
        self._currentDocument = None
        self._links = None
        self._clicking_link = False
        self._toolbar = None

    def createLayout(self):
        """Set up the main layout components.
        Returns the layout instance"""
        # main layout
        self._main_layout = layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # add an empty toolbar to the widget
        self._toolbar_layout = tb_layout = QHBoxLayout()
        layout.addLayout(tb_layout)
        tb_layout.addWidget(self.toolbar())
        tb_layout.addStretch(1)

        return layout

    def createHighlighters(self):
        self._highlightFormat = QTextCharFormat()
        self._highlightMusicFormat = Highlighter()
        self._highlightRange = None
        self._highlightTimer = QTimer(singleShot=True, interval= 250, timeout=self.updateHighlighting)
        self._highlightRemoveTimer = QTimer(singleShot=True, timeout=self.clearHighlighting)

    def createView(self):
        """Creates the actual View instance."""
        self.view = popplerview.View(self)
        self.readSettings()
        self.view.setViewMode(qpopplerview.FitWidth)
        surface = self.view.surface()
        surface.setPageLayout(qpopplerview.RowLayout())
        surface.linkClicked.connect(self.slotLinkClicked)
        surface.linkHovered.connect(self.slotLinkHovered)
        surface.linkLeft.connect(self.slotLinkLeft)
        surface.setShowUrlTips(False)
        surface.linkHelpRequested.connect(self.slotLinkHelpRequested)

        self.view.viewModeChanged.connect(self.updateZoomInfo)
        surface.pageLayout().scaleChanged.connect(self.updateZoomInfo)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.showContextMenu)

    def createContextMenu(self):
        """Creates the context menu.
        Subclasses should override this with their concrete menu."""
        raise NotImplementedError("Concrete Viewer class {} must implement 'createContextMenu'".format(
            type(self).__name__))

    def createHelpButton(self):
        """Create the viewer's help  button."""
        # The help button requires that the userguide page's filename
        # matches that of the viewer panel's classname
        # (e.g. ManuscriptViewPanel.md)
        self.helpButton = QToolButton(
            icon = icons.get("help-contents"),
            autoRaise = True,
            clicked = lambda: userguide.show(self.parent().viewerName()))

    def connectSlots(self):
        """Connects the slots of the viewer."""
        app.settingsChanged.connect(self.readSettings)

        # react if cursor of current text document moves
        self.parent().mainwindow().currentViewChanged.connect(self.slotCurrentViewChanged)
        view = self.parent().mainwindow().currentView()
        if view:
            self.slotCurrentViewChanged(view)

    def sizeHint(self):
        """Returns the initial size the PDF (Music) View prefers."""
        return self.parent().mainwindow().size() / 2

    def updateZoomInfo(self):
        """Called when zoom and viewmode of the qpopplerview change, emit zoomChanged."""
        self.zoomChanged.emit(self.view.viewMode(), self.view.surface().pageLayout().scale())

    def currentDocument(self):
        """Returns the current Document or None."""
        return self._currentDocument

    def setCurrentDocument(self, doc):
        """Set the current document."""
        self._currentDocument = doc

    def openDocument(self, doc):
        """Opens a documents.Document instance."""
        self.clear()
        self._currentDocument = doc
        document = doc.document()
        if document:
            self._links = pointandclick.links(document)
            self.view.load(document)
            position = self._positions.get(doc, (0, 0, 0))
            self.view.setPosition(position, True)

    def clear(self):
        """Empties the view."""
        cur = self._currentDocument
        if cur:
            self._positions[cur] = self.view.position()
        self._currentDocument = None
        self._links = None
        self._highlightRange = None
        self._highlightTimer.stop()
        self.view.clear()

    def readSettings(self):
        """Reads the settings from the user's preferences."""
        # background and highlight colors of music view
        colors = textformats.formatData('editor').baseColors
        self._highlightMusicFormat.setColor(colors['musichighlight'])
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
                from . import editinplace
                editinplace.edit(self, cursor, ev.globalPos())
            else:
                mainwindow = self.parent().mainwindow()
                self._clicking_link = True
                mainwindow.setTextCursor(cursor, findOpenView=True)
                self._clicking_link = False
                import widgets.blink
                widgets.blink.Blinker.blink_cursor(mainwindow.currentView())
                mainwindow.activateWindow()
                mainwindow.currentView().setFocus()
        elif (isinstance(link, popplerqt4.Poppler.LinkBrowse)
              and not link.url().startswith('textedit:')):
            helpers.openUrl(QUrl(link.url()))

    def slotLinkHovered(self, page, link):
        """Called when the mouse hovers a link.
        If the links points to the current editor document, the token(s) it points
        at are highlighted using a transparent selection color.
        The highlight shows for a few seconds but disappears when the mouse moves
        off the link or when the link is clicked.
        """
        self.view.surface().highlight(self._highlightMusicFormat,
            [(page, link.linkArea().normalized())], 2000)
        self._highlightRange = None
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
        self.clearHighlighting()
        view = self.parent().mainwindow().currentView()
        viewhighlighter.highlighter(view).clear(self._highlightFormat)

    def slotLinkHelpRequested(self, pos, page, link):
        """Called when a ToolTip wants to appear above the hovered link."""
        if isinstance(link, popplerqt4.Poppler.LinkBrowse):
            cursor = self._links.cursor(link)
            if cursor:
                from . import tooltip
                text = tooltip.text(cursor)
            elif link.url():
                l = textedit.link(link.url())
                if l:
                    text = "{0} ({1}:{2})".format(os.path.basename(l.filename), l.line, l.column)
                else:
                    text = link.url()
            QToolTip.showText(pos, text, self.view.surface(), page.linkRect(link.linkArea()))

    def slotCurrentViewChanged(self, view, old=None):
        self.view.surface().clearHighlight(self._highlightMusicFormat)
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
                center = rect.center()
                self.view.ensureVisible(center.x(), center.y(),
                                        50 + rect.width() // 2,
                                        50 + rect.height() // 2)

            # perform highlighting after move has been started. This is to ensure that if kinetic scrolling is
            # is enabled its speed is already set so that we can adjust the highlight timer.
            self.highlight(links.destinations(), s)


    def highlight(self, destinations, slice, msec=None):
        """(Internal) Highlights the from the specified destinations the specified slice."""
        count = slice.stop - slice.start
        if msec is None:
            # RC: increased timer to give some time to the kinetic scrolling to complete.
            kineticTimeLeft = 0
            if self.view.kineticScrollingEnabled():
                kineticTimeLeft = 20*self.view.kineticTicksLeft()
            msec = 5000 if count > 1 else 2000 # show selections longer
            msec += kineticTimeLeft
        self._highlightRemoveTimer.start(msec)
        if self._highlightRange == slice:
            return # don't redraw if same
        self._highlightRange = slice
        self._destinations = destinations[slice]
        if count > 100:
            self._highlightTimer.start()
        else:
            self._highlightTimer.stop()
            self.updateHighlighting()

    def updateHighlighting(self):
        """Really orders the view's surface to draw the highlighting."""
        layout = self.view.surface().pageLayout()
        areas = [(layout[pageNum], rect)
                    for dest in self._destinations
                    for pageNum, rect in dest]
        self.view.surface().highlight(self._highlightMusicFormat, areas)

    def clearHighlighting(self):
        """Called on timeout of the _highlightRemoveTimer."""
        self._highlightRange = None
        self.view.surface().clearHighlight(self._highlightMusicFormat)

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
        self.view.center(self.destinationsRect(links.destinations()[s]).center())
        self.highlight(links.destinations(), s, 10000)

    def destinationsRect(self, destinations):
        """Return the rectangle containing all destinations."""
        layout = self.view.surface().pageLayout()
        rect = QRect()
        for dest in destinations:
            for pageNum, r in dest:
                rect = rect.united(layout[pageNum].linkRect(r.normalized()))
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
            pos_in_surface = self.view.surface().mapFromGlobal(pos)
            page, link = self.view.surface().pageLayout().linkAt(pos_in_surface)
            if link:
                cursor = self._links.cursor(link, True)
        self._contextMenu.show(pos, link, cursor)

    def toolbar(self):
        """Returns the viewer's toolbar widget."""
        if not self._toolbar:
            self._toolbar = self.parent().mainwindow().addToolBar(self.parent().viewerName())
        return self._toolbar


class Highlighter(qpopplerview.Highlighter):
    """Simple version of qpopplerview.Highlighter that has the color settable.
    You must set a color before using the Highlighter.
    """
    def setColor(self, color):
        """Sets the color to use to draw highlighting rectangles."""
        self._color = color

    def color(self):
        """Returns the color set using the setColor method."""
        return self._color
