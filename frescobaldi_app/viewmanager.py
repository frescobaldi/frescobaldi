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
ViewManager is a QSplitter containing sub-splitters to display multiple
ViewSpaces.
ViewSpace is a QStackedWidget with a statusbar, capable of displaying one of
multiple views.
"""


import contextlib
import weakref

from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtWidgets import (
    QAction, QHBoxLayout, QLabel, QMenu, QProgressBar, QSplitter,
    QStackedWidget, QVBoxLayout, QWidget)

import actioncollection
import app
import icons
import view as view_
import qutil


class ViewStatusBar(QWidget):
    def __init__(self, parent=None):
        super(ViewStatusBar, self).__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(2, 1, 0, 1)
        layout.setSpacing(8)
        self.setLayout(layout)
        self.positionLabel = QLabel()
        layout.addWidget(self.positionLabel)

        self.stateLabel = QLabel()
        self.stateLabel.setFixedSize(16, 16)
        layout.addWidget(self.stateLabel)

        self.infoLabel = QLabel(minimumWidth=10)
        layout.addWidget(self.infoLabel, 1)

    def event(self, ev):
        if ev.type() == QEvent.MouseButtonPress:
            if ev.button() == Qt.RightButton:
                self.showContextMenu(ev.globalPos())
            else:
                self.parent().activeView().setFocus()
            return True
        return super(ViewStatusBar, self).event(ev)

    def showContextMenu(self, pos):
        menu = QMenu(self)
        menu.aboutToHide.connect(menu.deleteLater)
        viewspace = self.parent()
        manager = viewspace.manager()

        a = QAction(icons.get('view-split-top-bottom'), _("Split &Horizontally"), menu)
        menu.addAction(a)
        a.triggered.connect(lambda: manager.splitViewSpace(viewspace, Qt.Vertical))
        a = QAction(icons.get('view-split-left-right'), _("Split &Vertically"), menu)
        menu.addAction(a)
        a.triggered.connect(lambda: manager.splitViewSpace(viewspace, Qt.Horizontal))
        menu.addSeparator()
        a = QAction(icons.get('view-close'), _("&Close View"), menu)
        a.triggered.connect(lambda: manager.closeViewSpace(viewspace))
        a.setEnabled(manager.canCloseViewSpace())
        menu.addAction(a)

        menu.exec_(pos)


class ViewSpace(QWidget):
    """A ViewSpace manages a stack of views, one of them is visible.

    The ViewSpace also has a statusbar, accessible in the status attribute.
    The viewChanged(View) signal is emitted when the current view for this ViewSpace changes.

    Also, when a ViewSpace is created (e.g. when a window is created or split), the
    app.viewSpaceCreated(space) signal is emitted.

    You can use the app.viewSpaceCreated() and the ViewSpace.viewChanged() signals to implement
    things on a per ViewSpace basis, e.g. in the statusbar of a ViewSpace.

    """
    viewChanged = pyqtSignal(view_.View)

    def __init__(self, manager, parent=None):
        super(ViewSpace, self).__init__(parent)
        self.manager = weakref.ref(manager)
        self.views = []

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)
        self.status = ViewStatusBar(self)
        self.status.setEnabled(False)
        layout.addWidget(self.status)
        app.languageChanged.connect(self.updateStatusBar)
        app.viewSpaceCreated(self)

    def activeView(self):
        if self.views:
            return self.views[-1]

    def document(self):
        """Returns the currently active document in this space.

        If there are no views, returns None.

        """
        if self.views:
            return self.views[-1].document()

    def showDocument(self, doc):
        """Shows the document, creating a View if necessary."""
        if doc is self.document():
            return
        cur = self.activeView()
        for view in self.views[:-1]:
            if doc is view.document():
                self.views.remove(view)
                break
        else:
            view = view_.View(doc)
            self.stack.addWidget(view)
        self.views.append(view)
        if cur:
            self.disconnectView(cur)
        self.connectView(view)
        self.stack.setCurrentWidget(view)
        self.updateStatusBar()

    def removeDocument(self, doc):
        active = doc is self.document()
        if active:
            self.disconnectView(self.activeView())
        for view in self.views:
            if doc is view.document():
                self.views.remove(view)
                view.deleteLater()
                break
        else:
            return
        if active and self.views:
            self.connectView(self.views[-1])
            self.stack.setCurrentWidget(self.views[-1])
            self.updateStatusBar()

    def connectView(self, view):
        view.installEventFilter(self)
        view.cursorPositionChanged.connect(self.updateCursorPosition)
        view.modificationChanged.connect(self.updateModificationState)
        view.document().urlChanged.connect(self.updateDocumentName)
        self.viewChanged.emit(view)

    def disconnectView(self, view):
        view.removeEventFilter(self)
        view.cursorPositionChanged.disconnect(self.updateCursorPosition)
        view.modificationChanged.disconnect(self.updateModificationState)
        view.document().urlChanged.disconnect(self.updateDocumentName)

    def eventFilter(self, view, ev):
        if ev.type() == QEvent.FocusIn:
            self.setActiveViewSpace()
        return False

    def setActiveViewSpace(self):
        self.manager().setActiveViewSpace(self)

    def updateStatusBar(self):
        """Update all info in the statusbar, e.g. on document change."""
        if self.views:
            self.updateCursorPosition()
            self.updateModificationState()
            self.updateDocumentName()

    def updateCursorPosition(self):
        cur = self.activeView().textCursor()
        line = cur.blockNumber() + 1
        try:
            column = cur.positionInBlock()
        except AttributeError: # only in very recent PyQt5
            column = cur.position() - cur.block().position()
        self.status.positionLabel.setText(_("Line: {line}, Col: {column}").format(
            line = line, column = column))

    def updateModificationState(self):
        modified = self.document().isModified()
        pixmap = icons.get('document-save').pixmap(16) if modified else QPixmap()
        self.status.stateLabel.setPixmap(pixmap)

    def updateDocumentName(self):
        self.status.infoLabel.setText(self.document().documentName())


class ViewManager(QSplitter):

    # This signal is always emitted on setCurrentDocument,
    # even if the view is the same as before.
    # use MainWindow.currentViewChanged() to be informed about
    # real View changes.
    viewChanged = pyqtSignal(view_.View)

    # This signal is emitted when another ViewSpace becomes active.
    activeViewSpaceChanged = pyqtSignal(ViewSpace, ViewSpace)

    def __init__(self, parent=None):
        super(ViewManager, self).__init__(parent)
        self._viewSpaces = []

        viewspace = ViewSpace(self)
        viewspace.status.setEnabled(True)
        self.addWidget(viewspace)
        self._viewSpaces.append(viewspace)

        self.createActions()
        app.documentClosed.connect(self.slotDocumentClosed)

    def setCurrentDocument(self, doc, findOpenView=False):
        if doc is not self.activeViewSpace().document():
            done = False
            if findOpenView:
                for space in self._viewSpaces[-2::-1]:
                    if doc is space.document():
                        done = True
                        self.setActiveViewSpace(space)
                        break
            if not done:
                self.activeViewSpace().showDocument(doc)
        self.viewChanged.emit(self.activeViewSpace().activeView())
        # the active space now displays the requested document
        # now also set this document in spaces that are empty
        for space in self._viewSpaces[:-1]:
            if not space.document():
                space.showDocument(doc)
        self.focusActiveView()

    def focusActiveView(self):
        self.activeViewSpace().activeView().setFocus()

    def setActiveViewSpace(self, space):
        prev = self._viewSpaces[-1]
        if space is prev:
            return
        self._viewSpaces.remove(space)
        self._viewSpaces.append(space)
        prev.status.setEnabled(False)
        space.status.setEnabled(True)
        self.activeViewSpaceChanged.emit(space, prev)
        self.viewChanged.emit(space.activeView())

    def slotDocumentClosed(self, doc):
        activeDocument = self.activeViewSpace().document()
        for space in self._viewSpaces:
            space.removeDocument(doc)
        if doc is not activeDocument:
            # setCurrentDocument will not be called, fill empty spaces with our
            # document.
            for space in self._viewSpaces[:-1]:
                if not space.document():
                    space.showDocument(activeDocument)

    def createActions(self):
        self.actionCollection = ac = ViewActions()
        # connections
        ac.window_close_view.setEnabled(False)
        ac.window_close_others.setEnabled(False)
        ac.window_split_horizontal.triggered.connect(self.splitCurrentVertical)
        ac.window_split_vertical.triggered.connect(self.splitCurrentHorizontal)
        ac.window_close_view.triggered.connect(self.closeCurrent)
        ac.window_close_others.triggered.connect(self.closeOthers)
        ac.window_next_view.triggered.connect(self.nextViewSpace)
        ac.window_previous_view.triggered.connect(self.previousViewSpace)

    def splitCurrentVertical(self):
        self.splitViewSpace(self.activeViewSpace(), Qt.Vertical)

    def splitCurrentHorizontal(self):
        self.splitViewSpace(self.activeViewSpace(), Qt.Horizontal)

    def closeCurrent(self):
        self.closeViewSpace(self.activeViewSpace())

    def closeOthers(self):
        for space in self._viewSpaces[-2::-1]:
            self.closeViewSpace(space)

    def nextViewSpace(self):
        self.focusNextChild()

    def previousViewSpace(self):
        self.focusPreviousChild()

    def activeViewSpace(self):
        return self._viewSpaces[-1]

    def splitViewSpace(self, viewspace, orientation):
        """Split the given view.

        If orientation == Qt.Horizontal, adds a new view to the right.
        If orientation == Qt.Vertical, adds a new view to the bottom.

        """
        active = viewspace is self.activeViewSpace()
        splitter = viewspace.parentWidget()
        newspace = ViewSpace(self)

        if splitter.count() == 1:
            splitter.setOrientation(orientation)
            size = splitter.sizes()[0]
            splitter.addWidget(newspace)
            splitter.setSizes([size / 2, size / 2])
        elif splitter.orientation() == orientation:
            index = splitter.indexOf(viewspace)
            splitter.insertWidget(index + 1, newspace)
        else:
            index = splitter.indexOf(viewspace)
            newsplitter = QSplitter()
            newsplitter.setOrientation(orientation)
            sizes = splitter.sizes()
            splitter.insertWidget(index, newsplitter)
            newsplitter.addWidget(viewspace)
            splitter.setSizes(sizes)
            size = newsplitter.sizes()[0]
            newsplitter.addWidget(newspace)
            newsplitter.setSizes([size / 2, size / 2])
        self._viewSpaces.insert(0, newspace)
        newspace.showDocument(viewspace.document())
        if active:
            newspace.activeView().setFocus()
        self.actionCollection.window_close_view.setEnabled(self.canCloseViewSpace())
        self.actionCollection.window_close_others.setEnabled(self.canCloseViewSpace())

    def closeViewSpace(self, viewspace):
        """Closes the given view."""
        active = viewspace is self.activeViewSpace()
        if active:
            self.setActiveViewSpace(self._viewSpaces[-2])
        splitter = viewspace.parentWidget()
        if splitter.count() > 2:
            viewspace.setParent(None)
            viewspace.deleteLater()
        elif splitter is self:
            if self.count() < 2:
                return
            # we contain only one other widget.
            # if that is a QSplitter, add all its children to ourselves
            # and copy the sizes and orientation.
            other = self.widget(1 - self.indexOf(viewspace))
            viewspace.setParent(None)
            viewspace.deleteLater()
            if isinstance(other, QSplitter):
                sizes = other.sizes()
                self.setOrientation(other.orientation())
                while other.count():
                    self.insertWidget(0, other.widget(other.count()-1))
                other.setParent(None)
                other.deleteLater()
                self.setSizes(sizes)
        else:
            # this splitter contains only one other widget.
            # if that is a ViewSpace, just add it to the parent splitter.
            # if it is a splitter, add all widgets to the parent splitter.
            other = splitter.widget(1 - splitter.indexOf(viewspace))
            parent = splitter.parentWidget()
            sizes = parent.sizes()
            index = parent.indexOf(splitter)

            if isinstance(other, ViewSpace):
                parent.insertWidget(index, other)
            else:
                #QSplitter
                sizes[index:index+1] = other.sizes()
                while other.count():
                    parent.insertWidget(index, other.widget(other.count()-1))
            viewspace.setParent(None)
            splitter.setParent(None)
            viewspace.deleteLater()
            splitter.deleteLater()
            parent.setSizes(sizes)
        self._viewSpaces.remove(viewspace)
        self.actionCollection.window_close_view.setEnabled(self.canCloseViewSpace())
        self.actionCollection.window_close_others.setEnabled(self.canCloseViewSpace())

    def canCloseViewSpace(self):
        return bool(self.count() > 1)




class ViewActions(actioncollection.ActionCollection):
    name = "view"
    def createActions(self, parent=None):
        self.window_split_horizontal = QAction(parent)
        self.window_split_vertical = QAction(parent)
        self.window_close_view = QAction(parent)
        self.window_close_others = QAction(parent)
        self.window_next_view = QAction(parent)
        self.window_previous_view = QAction(parent)

        # icons
        self.window_split_horizontal.setIcon(icons.get('view-split-top-bottom'))
        self.window_split_vertical.setIcon(icons.get('view-split-left-right'))
        self.window_close_view.setIcon(icons.get('view-close'))
        self.window_next_view.setIcon(icons.get('go-next-view'))
        self.window_previous_view.setIcon(icons.get('go-previous-view'))

        # shortcuts
        self.window_close_view.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_W)
        self.window_next_view.setShortcuts(QKeySequence.NextChild)
        qutil.removeShortcut(self.window_next_view, "Ctrl+,")
        self.window_previous_view.setShortcuts(QKeySequence.PreviousChild)
        qutil.removeShortcut(self.window_previous_view, "Ctrl+.")

    def translateUI(self):
        self.window_split_horizontal.setText(_("Split &Horizontally"))
        self.window_split_vertical.setText(_("Split &Vertically"))
        self.window_close_view.setText(_("&Close Current View"))
        self.window_close_others.setText(_("Close &Other Views"))
        self.window_next_view.setText(_("&Next View"))
        self.window_previous_view.setText(_("&Previous View"))

