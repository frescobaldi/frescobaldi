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
The tab bar with the documents.
"""


import platform

from PyQt6.QtCore import QSettings, Qt, QUrl, pyqtSignal
from PyQt6.QtWidgets import QMenu, QTabBar

import app
import icons
import document
import documentcontextmenu
import documenticon
import engrave
import util


class TabBar(QTabBar):
    """The tabbar above the editor window."""

    currentDocumentChanged = pyqtSignal(document.Document)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMovable(True)      # TODO: make configurable
        self.setExpanding(False)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.TextElideMode.ElideNone)

        mainwin = self.window()
        self.docs = []
        for doc in app.documents:
            self.addDocument(doc)
            if doc is mainwin.currentDocument():
                self.setCurrentDocument(doc)

        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        app.jobStarted.connect(self.setDocumentStatus)
        app.jobFinished.connect(self.setDocumentStatus)
        app.settingsChanged.connect(self.readSettings)
        engrave.engraver(mainwin).stickyChanged.connect(self.setDocumentStatus)
        mainwin.currentDocumentChanged.connect(self.setCurrentDocument)
        self.currentChanged.connect(self.slotCurrentChanged)
        self.tabMoved.connect(self.slotTabMoved)
        self.tabCloseRequested.connect(self.slotTabCloseRequested)
        self.readSettings()

        style = """
QTabBar::tab {
    background: white;
    border-style: solid;
    border-width: 1px 0px;
    border-color: #ACACAC;
    min-width: 8ex;
    padding: 2px 4px 2px 2px;
}

QTabBar::tab:selected:active {
    border-color: #045FFF;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #69B1FA, stop: 1 #0C80FF);
    color: white;
}

QTabBar::tab:selected:!active {
    background: #E5E5E5;
}

QTabBar::tab:first,
QTabBar::tab:only-one {
    border-left-width: 1px;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}

QTabBar::tab:!first:!selected:!previous-selected {
    border-left-color: #E5E5E5;
    border-left-width: 1px;
}

QTabBar::tab:last,
QTabBar::tab:only-one {
    border-right-width: 1px;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}
"""
        if platform.system() == "Darwin":
            self.setStyleSheet(style)

    def readSettings(self):
        """Called on init, and when the user changes the settings."""
        s = QSettings()
        self.setTabsClosable(s.value("tabs_closable", True, bool))

    def documents(self):
        return list(self.docs)

    def addDocument(self, doc):
        if doc not in self.docs:
            self.docs.append(doc)
            self.blockSignals(True)
            self.addTab('')
            self.blockSignals(False)
            self.setDocumentStatus(doc)

    def removeDocument(self, doc):
        if doc in self.docs:
            index = self.docs.index(doc)
            self.docs.remove(doc)
            self.blockSignals(True)
            self.removeTab(index)
            self.blockSignals(False)

    def setDocumentStatus(self, doc):
        if doc in self.docs:
            index = self.docs.index(doc)
            text = doc.documentName().replace('&', '&&')
            if self.tabText(index) != text:
                self.setTabText(index, text)
            tooltip = util.path(doc.url())
            self.setTabToolTip(index, tooltip)
            self.setTabIcon(index, documenticon.icon(doc, self.window()))

    def setCurrentDocument(self, doc):
        """ Raise the tab belonging to this document."""
        if doc in self.docs:
            index = self.docs.index(doc)
            self.blockSignals(True)
            self.setCurrentIndex(index)
            self.blockSignals(False)

    def slotCurrentChanged(self, index):
        """ Called when the user clicks a tab. """
        self.currentDocumentChanged.emit(self.docs[index])

    def slotTabCloseRequested(self, index):
        """ Called when the user clicks the close button. """
        self.window().closeDocument(self.docs[index])

    def slotTabMoved(self, index_from, index_to):
        """ Called when the user moved a tab. """
        doc = self.docs.pop(index_from)
        self.docs.insert(index_to, doc)

    def nextDocument(self):
        """ Switches to the next document. """
        index = self.currentIndex() + 1
        if index == self.count():
            index = 0
        self.setCurrentIndex(index)

    def previousDocument(self):
        index = self.currentIndex() - 1
        if index < 0:
            index = self.count() - 1
        self.setCurrentIndex(index)

    def contextMenuEvent(self, ev):
        index = self.tabAt(ev.pos())
        if index >= 0:
            self.contextMenu().exec_(self.docs[index], ev.globalPos())

    def contextMenu(self):
        try:
            return self._contextMenu
        except AttributeError:
            import documentcontextmenu
            self._contextMenu = documentcontextmenu.DocumentContextMenu(
                self.window())
        return self._contextMenu
