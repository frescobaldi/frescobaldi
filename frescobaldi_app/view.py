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
View is basically a QPlainTextEdit instance.
ViewSpace is a QStackedWidget with a statusbar, capable of displaying one of
multiple views.
ViewManager is a QSplitter containing sub-splitters to display multiple
ViewSpaces.
"""

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons
import document


class View(QPlainTextEdit):
    
    focusIn = pyqtSignal(QPlainTextEdit)
    
    def __init__(self, document):
        super(View, self).__init__()
        self.setDocument(document)
        
    def focusInEvent(self, ev):
        super(View, self).focusInEvent(ev)
        self.focusIn.emit(self)
        



class ViewStatusBar(QWidget):
    def __init__(self, parent=None):
        super(ViewStatusBar, self).__init__(parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 1, 0, 1)
        layout.setSpacing(4)
        self.setLayout(layout)
        self.pos = QLabel()
        text = _("Line: {line}, Col: {column}").format(line=9999, column=99)
        self.pos.setMinimumWidth(self.pos.fontMetrics().width(text))
        layout.addWidget(self.pos)
        
        self.state = QLabel()
        self.state.setFixedSize(16, 16)
        layout.addWidget(self.state)
        
        self.info = QLabel()
        layout.addWidget(self.info, 1)
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(14)
        layout.addWidget(self.progress, 1)
        


class ViewSpace(QWidget):
    def __init__(self, manager, parent=None):
        super(ViewSpace, self).__init__(parent)
        self.manager = manager
        self._activeView = None
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)
        self.status = ViewStatusBar(self)
        layout.addWidget(self.status)
        
    def activeView(self):
        return self._activeView

    def addView(self, view):
        self.stack.addWidget(view)
        
    def removeView(self, view):
        if view is self._activeView:
            self.connectView(view, False)
            self._activeView = None
        self.stack.removeWidget(view)
        
    def setActiveView(self, view):
        if view is self._activeView:
            return
        if self._activeView:
            self.connectView(self._activeView, False)
        self.stack.setCurrentWidget(view)
        self._activeView = view
        self.connectView(view)
        self.updateStatusBar()
    
    def connectView(self, view, disconnect=False):
        if disconnect:
            view.cursorPositionChanged.disconnect(self.updateStatusBar)
            view.modificationChanged.disconnect(self.updateStatusBar)
            view.focusIn.disconnect(self.setActiveViewSpace)
        else:
            view.cursorPositionChanged.connect(self.updateStatusBar)
            view.modificationChanged.connect(self.updateStatusBar)
            view.focusIn.connect(self.setActiveViewSpace)
    
    def setActiveViewSpace(self, view):
        self.manager.setActiveViewSpace(self)
        
    def updateStatusBar(self):
        view = self.activeView()
        if view:
            cur = view.textCursor()
            self.status.pos.setText(_("Line: {line}, Col: {column}").format(
                line = cur.blockNumber() + 1,
                column = cur.columnNumber()))
            if view.document().isModified():
                pixmap = icons.get('document-save').pixmap(16)
            else:
                pixmap = QPixmap()
            self.status.state.setPixmap(pixmap)
            
    def views(self):
        return map(self.stack.widget, range(self.stack.count()))
        
    def showDocument(self, doc):
        for view in self.views():
            if view.document() is doc:
                break
        else:
            view = View(doc)
            self.addView(view)
        self.setActiveView(view)
        




class ViewManager(QSplitter):
    
    documentChanged = pyqtSignal(document.Document)
    
    def __init__(self, parent=None):
        super(ViewManager, self).__init__(parent)
        self._viewSpaces = []
        
        viewspace = ViewSpace(self)
        self.addWidget(viewspace)
        self._viewSpaces.append(viewspace)
        print self._viewSpaces

    
    def activeViewSpace(self):
        return self._viewSpaces[-1]
        
    def activeView(self):
        return self.activeViewSpace().activeView()
    
    def setActiveViewSpace(self, space):
        prev = self.activeViewSpace()
        if space is prev:
            return
        self._viewSpaces.remove(space)
        self._viewSpaces.append(space)
        
        prev.status.setEnabled(False)
        space.status.setEnabled(True)
        newdoc = space.activeView().document()
        if prev.activeView().document() is not newdoc:
            self.documentChanged.emit(newdoc)
        space.activeView().setFocus()

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
            sizes = splitter.sizes()
            splitter.insertWidget(index + 1, newspace)
            sizes[index:index+1] = [sizes[index] / 2, sizes[index] / 2]
            splitter.setSizes(sizes)
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
        newview = View(viewspace.activeView().document())
        newspace.addView(newview)
        newspace.setActiveView(newview)
        if active:
            self.setActiveViewSpace(newspace)
        
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
        
    def canCloseViewSpace(self):
        return bool(self.count() > 1)
        
    def showDocument(self, doc):
        view = self.activeView()
        if view and view.document() is doc:
            return
        self.activeViewSpace().showDocument(doc)
        self.documentChanged.emit(doc)


