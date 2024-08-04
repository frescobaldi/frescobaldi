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
Abstract base class for a Poppler based viewer widget.
"""


import collections
import os
import weakref

from PyQt6.QtCore import pyqtSignal, QMargins, QPoint, QRect, Qt, QTimer, QUrl
from PyQt6.QtGui import QCursor, QTextCharFormat
from PyQt6.QtWidgets import (
    QToolTip, QVBoxLayout, QHBoxLayout, QWidget, QToolBar)

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
import helpers
import textedit
import textformats
import contextmenu
import viewhighlighter
import widgets.dialog
import userguide

from . import abstractviewwidget
from . import documents
from . import pointandclick


class AbstractPopplerWidget(abstractviewwidget.AbstractViewWidget):
    """Widget containing the qpageview.View."""

    # TODO: As much as possible should be moved to the base class.

    zoomChanged = pyqtSignal(int, float) # mode, scale

    def __init__(self, panel):
        """Creates the Poppler View for the panel."""
        super().__init__(panel)
        self.actionCollection = panel.actionCollection
        self.createProtectedFields()
        self.createLayout()
        self._toolbar = self.createToolbar()
        self._main_layout.addWidget(self._toolbar)
        self.createHighlighters()
        self.createView()
        self.createContextMenu()
        self.connectSlots()

        # load current session when the widget is created
        import sessions
        cs = sessions.currentSession()
        if cs:
            self.slotSessionChanged(cs)
        self.readSettings()

        userguide.openWhatsThis(self)
        app.translateUI(self)

    def createProtectedFields(self):
        """Create the empty protected fields that will hold actual data."""
        self._links = None
        self._clicking_link = False
        self._toolbar = None

    def createLayout(self):
        """Set up the main layout component."""
        self._main_layout = layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createToolbar(self):
        """Factory method to create a toolbar."""
        raise NotImplementedError()

    def createHighlighters(self):
        self._highlightFormat = QTextCharFormat()
        self._highlightMusicFormat = qpageview.highlight.Highlighter()
        self._highlightRange = None

    def createView(self):
        """Creates the actual View instance."""
        self.view = pagedview.PagedView(self)
        self.view.setRubberband(qpageview.rubberband.Rubberband())
        self._main_layout.addWidget(self.view)
        self.view.setViewMode(qpageview.FitWidth)

        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.showContextMenu)

    def createContextMenu(self):
        """Creates the context menu.
        Subclasses should override this with their concrete menu."""
        raise NotImplementedError("Concrete Viewer class {} must implement 'createContextMenu'".format(
            type(self).__name__))

    def translateUI(self):
        self.setWhatsThis(
            "<p>This viewer doesn't have a What'sThis info set.</p>")

    def connectSlots(self):
        """Connects the slots of the viewer."""
        app.settingsChanged.connect(self.readSettings)
        app.sessionChanged.connect(self.slotSessionChanged)
        app.saveSessionData.connect(self.slotSaveSessionData)

        # react if cursor of current text document moves
        self.parent().mainwindow().currentViewChanged.connect(self.slotCurrentViewChanged)
        view = self.parent().mainwindow().currentView()
        if view:
            self.slotCurrentViewChanged(view)

        self.view.linkClicked.connect(self.slotLinkClicked)
        self.view.linkHovered.connect(self.slotLinkHovered)
        self.view.linkLeft.connect(self.slotLinkLeft)
        self.view.linkHelpRequested.connect(self.slotLinkHelpRequested)

    def viewerName(self):
        """Return the viewerName() attribute of the panel."""
        if not hasattr(self, '_viewerName'):
            self._viewerName = self.parent().viewerName()
        return self._viewerName

    def sizeHint(self):
        """Returns the initial size the PDF (Music) View prefers."""
        return self.parent().mainwindow().size() / 2

    def currentViewdoc(self):
        """Returns the current Document or None."""
        return self.view.document()

    def openViewdoc(self, doc):
        """Opens a qpageview.Document instance."""
        try:
            self.view.setDocument(doc)
            document = doc.document()
            doc.ispresent = True
            if document:
                self._links = pointandclick.links(document)
        except OSError:
            # the file is not found on the given path
            dlg = widgets.dialog.Dialog(buttons=('yes', 'no'))
            dlg.setWindowTitle("Missing file")
            fn = doc.filename()
            dlg.setMessage(_("The file {filename} is missing.\n\n"
                "Do you want to remove the filename from the list?").format(filename=fn))
            dlg.setIcon("question")
            dlg.setToolTip(_(
                "Answering 'No' will give you a chance to restore the "
                "file without having to re-add it."))
            if dlg.exec_():
                mds = self.actionCollection.viewer_document_select
                mds.removeViewdoc(doc)
            else:
                doc.ispresent = False

    def clear(self):
        """Empties the view."""
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
        if ev.button() == Qt.MouseButton.RightButton:
            return
        cursor = self._links.cursor(link, True)
        if cursor:
            if ev.modifiers() & Qt.KeyboardModifier.ShiftModifier:
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
                    text = f"{os.path.basename(l.filename)} ({l.line}:{l.column})"
                else:
                    text = link.url
        elif hasattr(link, "linkobj") and isinstance(link.linkobj, popplerqt5.Poppler.LinkGoto):
            text = _("Page {num}").format(num=link.linkobj.destination().pageNumber())
            if link.linkobj.isExternal():
                text = link.linkobj.fileName() + "\n" + text
        else:
            return
        QToolTip.showText(pos, text, self.view, page.linkRect(link))

    def slotSessionChanged(self, name):
        """Called whenever the current session is changed
        (also on application startup or after a session is created).
        If the session already exists load manuscripts from the
        session object and load them in the viewer."""
        if name:
            import sessions
            import qsettings
            g = sessions.sessionGroup(name)
            if g.contains("urls"): # the session is not new
                ds = self.actionCollection.viewer_document_select
                ds.removeAllViewdocs(update = False)
                self.clear()
                viewdocs = []
                files_key = f"{self.viewerName()}-documents"
                active_file = ""
                for i in range(g.beginReadArray(files_key)):
                    g.setArrayIndex(i)
                    filename = g.value("filename", "", str)
                    if filename:
                        doc = pagedview.loadPdf(filename)
                        viewdocs.append(doc)
                        # can it load?
                        doc.ispresent = os.path.isfile(filename)
                        if g.value("isactive", False, bool):
                            active_file = filename
                        props = self.view.properties().load(g)
                        self.view.documentPropertyStore.set(doc, props)
                ds.loadViewdocs(viewdocs,
                    active_viewdoc = active_file,
                    sort = False) # may be replaced by a Preference

    def slotSaveSessionData(self):
        """Saves the filenames and positions of the open manuscripts.
        If a file doesn't have a position (because it hasn't been moved or
        shown) a default position is stored."""
        import sessions
        g = sessions.currentSessionGroup()
        if g:
            # TODO: cleanup for multi-file documents later
            files_key = f"{self.viewerName()}-documents"
            docs = self.actionCollection.viewer_document_select.viewdocs()
            if docs:
                current = self.currentViewdoc()
                g.beginWriteArray(files_key, len(docs))
                for i, doc in enumerate(docs):
                    g.setArrayIndex(i)
                    g.setValue("filename", doc.filename())
                    g.setValue("isactive", doc is current)
                    if doc is current:
                        self.view.documentPropertyStore.set(doc,
                            self.view.properties().get(self.view))
                    props = self.view.documentPropertyStore.get(doc)
                    if props:
                        props.save(g)
                g.endArray()
            else:
                g.remove(files_key)

    def slotCurrentViewChanged(self, view, old=None):
        self.view.clearHighlight(self._highlightMusicFormat)
        if old:
            old.cursorPositionChanged.disconnect(self.slotCursorPositionChanged)
        view.cursorPositionChanged.connect(self.slotCursorPositionChanged)

    def slotCursorPositionChanged(self):
        """Called when the user moves the text cursor."""
        self.showCurrentLinks(
            not self._clicking_link
            and self.parent().actionCollection.viewer_sync_cursor.isChecked())

    def showCurrentLinks(self, scroll=False, msec=None):
        """Show objects at current text cursor.

        If scroll is True, also scrolls the view if needed. If msec is given,
        objects are highlighed that long. If not given, a default time is used.

        """
        if not self.isVisible() or not self._links:
            return # not visible of no PDF in the viewer

        view = self.parent().mainwindow().currentView()
        links = self._links.boundLinks(view.document())
        if not links:
            return # the PDF contains no references to the current text document

        s = links.indices(view.textCursor())
        if not s:
            if s is False:
                self.view.clearHighlight(self._highlightMusicFormat)
            return

        if not scroll and self._highlightRange == s and self.view.isHighlighting(self._highlightMusicFormat):
            return # don't redraw if same
        self._highlightRange = s

        # create the dict of areas
        layout = self.view.pageLayout()
        areas = collections.defaultdict(list)
        for dest in links.destinations()[s]:
            for pageNum, rect in dest:
                areas[layout[pageNum]].append(rect)

        if scroll:
            # compute the bounding rect
            boundingRect = QRect()
            for page, rects in areas.items():
                f = page.mapToPage(1, 1).rect
                pbound = QRect()
                for r in rects:
                    pbound |= f(r)
                boundingRect |= pbound.translated(page.pos())
            self.view.ensureVisible(boundingRect, QMargins(20, 20, 20, 20))

        if msec is None:
            msec = 5000 if s.stop - s.start > 1 else 2000 # show selections longer
        # RC: increased timer to give some time to the kinetic scrolling to complete.
        if self.view.isScrolling():
            msec += self.view.remainingScrollTime()
        self.view.highlight(areas, self._highlightMusicFormat, msec)

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
        self._contextMenu.show(pos, link, cursor)

    def toolbar(self):
        """Returns the viewer's toolbar widget."""
        return self._toolbar
