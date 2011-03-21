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
The PDF preview panel.
"""

import os
import weakref

from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QAction, QComboBox, QPalette, QKeySequence, QWidgetAction

import app
import actioncollection
import actioncollectionmanager
import icons
import panels
import resultfiles

from . import documents


# default zoom percentages
_zoomvalues = [50, 75, 100, 125, 150, 175, 200, 250, 300]


class MusicViewPanel(panels.Panel):
    def __init__(self, mainwindow):
        super(MusicViewPanel, self).__init__(mainwindow)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+M"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        
        ac = self.actionCollection = Actions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.music_print.triggered.connect(self.printMusic)
        ac.music_zoom_in.triggered.connect(self.zoomIn)
        ac.music_zoom_out.triggered.connect(self.zoomOut)
        ac.music_fit_width.triggered.connect(self.fitWidth)
        ac.music_fit_height.triggered.connect(self.fitHeight)
        ac.music_fit_both.triggered.connect(self.fitBoth)
        ac.music_document_select.currentDocumentChanged.connect(self.openDocument)
        ac.music_document_select.documentsChanged.connect(self.updateActions)
        ac.music_document_select.documentClosed.connect(self.closeDocument)
        
    def translateUI(self):
        self.setWindowTitle(_("Music View"))
        self.toggleViewAction().setText(_("&Music View"))
    
    def createWidget(self):
        import widget
        return widget.MusicView(self)
        
    def openDocument(self, doc):
        """Opens the documents.Document instance (wrapping a lazily loaded Poppler document)."""
        self.widget().openDocument(doc)
    
    def closeDocument(self):
        self.widget().clear()
        
    def updateActions(self):
        ac = self.actionCollection
        ac.music_print.setEnabled(bool(ac.music_document_select.documents()))
        
    def printMusic(self):
        pass
    
    def zoomIn(self):
        self.widget().view.zoomIn()
    
    def zoomOut(self):
        self.widget().view.zoomOut()
    
    def fitWidth(self):
        import qpopplerview
        self.widget().view.setViewMode(qpopplerview.FitWidth)
    
    def fitHeight(self):
        import qpopplerview
        self.widget().view.setViewMode(qpopplerview.FitHeight)

    def fitBoth(self):
        import qpopplerview
        self.widget().view.setViewMode(qpopplerview.FitBoth)


class Actions(actioncollection.ActionCollection):
    name = "musicview"
    def createActions(self, panel):
        self.music_document_select = DocumentChooserAction(panel)
        self.music_print = QAction(panel)
        self.music_zoom_in = QAction(panel)
        self.music_zoom_out = QAction(panel)
        self.music_zoom_combo = ZoomerAction(panel)
        self.music_fit_width = QAction(panel)
        self.music_fit_height = QAction(panel)
        self.music_fit_both = QAction(panel)
        
        self.music_fit_width.setCheckable(True)
        self.music_fit_height.setCheckable(True)
        self.music_fit_both.setCheckable(True)

        self.music_print.setIcon(icons.get('document-print'))
        self.music_zoom_in.setIcon(icons.get('zoom-in'))
        self.music_zoom_out.setIcon(icons.get('zoom-out'))
        self.music_fit_width.setIcon(icons.get('zoom-fit-width'))
        self.music_fit_height.setIcon(icons.get('zoom-fit-height'))
        self.music_fit_both.setIcon(icons.get('zoom-fit-best'))
        
        self.music_document_select.setShortcut(QKeySequence(Qt.SHIFT | Qt.CTRL | Qt.Key_O))
        self.music_print.setShortcuts(QKeySequence.Print)
        self.music_zoom_in.setShortcuts(QKeySequence.ZoomIn)
        self.music_zoom_out.setShortcuts(QKeySequence.ZoomOut)
        
    def translateUI(self):
        self.music_document_select.setText(_("Select Music View Document"))
        self.music_print.setText(_("&Print Music..."))
        self.music_zoom_in.setText(_("Zoom &In"))
        self.music_zoom_out.setText(_("Zoom &Out"))
        self.music_fit_width.setText(_("Fit &Width"))
        self.music_fit_height.setText(_("Fit &Height"))
        self.music_fit_both.setText(_("Fit &Page"))
        

class DocumentChooserAction(QWidgetAction):
    
    documentClosed = pyqtSignal()
    documentsChanged = pyqtSignal()
    currentDocumentChanged = pyqtSignal(documents.Document)
    
    def __init__(self, panel):
        super(DocumentChooserAction, self).__init__(panel)
        self.triggered.connect(self.showPopup)
        self._document = lambda: None
        self._documents = []
        self._currentIndex = -1
        self._indices = weakref.WeakKeyDictionary()
        panel.mainwindow().currentDocumentChanged.connect(self.setDocument)
        documents.documentUpdated.connect(self.setDocument)
        
    def createWidget(self, parent):
        return DocumentChooser(self, parent)
    
    def showPopup(self):
        """Called when our action is triggered by a keyboard shortcut."""
        # find the widget in our floating panel, if available there
        for w in self.createdWidgets():
            if w.window() == self.parent():
                w.showPopup()
                return
        # find the one in the main window
        for w in self.createdWidgets():
            if w.window() == self.parent().mainwindow():
                w.showPopup()
                return
    
    def setDocument(self, document):
        """Displays the DocumentGroup of the given document in our chooser."""
        prev = self._document()
        self._document = weakref.ref(document)
        if prev:
            prev.loaded.disconnect(self.updateDocument)
            prev.closed.disconnect(self.closeDocument)
            self._indices[prev] = self._currentIndex
        document.loaded.connect(self.updateDocument)
        document.closed.connect(self.closeDocument)
        self.updateDocument()
        
    def updateDocument(self):
        """(Re)read the output documents of the current document and show them."""
        docs = self._documents = documents.group(self._document()).documents()
        self.setVisible(bool(docs))
        self.setEnabled(bool(docs))
        for w in self.createdWidgets():
            w.updateContents(self)
        
        index = self._indices.get(self._document(), 0)
        if index < 0 or index >= len(docs):
            index = 0
        self.documentsChanged.emit()
        self.setCurrentIndex(index)
    
    def closeDocument(self):
        """Called when the current document is closed by the user."""
        self.documentClosed.emit()
        
    def documents(self):
        return self._documents
        
    def setCurrentIndex(self, index):
        if self._documents:
            self._currentIndex = index
            for w in self.createdWidgets():
                w.setCurrentIndex(index)
            self.currentDocumentChanged.emit(self._documents[index])
    
    def currentIndex(self):
        return self._currentIndex
        

class DocumentChooser(QComboBox):
    def __init__(self, action, parent):
        super(DocumentChooser, self).__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setFocusPolicy(Qt.NoFocus)
        self.activated[int].connect(action.setCurrentIndex)
        self.updateContents(action)
        app.translateUI(self)
        
    def translateUI(self):
        self.setToolTip(_("Choose the PDF document to display."))

    def updateContents(self, action):
        self.clear()
        self.addItems([os.path.basename(doc.filename()) for doc in action.documents()])
        self.setCurrentIndex(action.currentIndex())


class ZoomerAction(QWidgetAction):
    def __init__(self, panel):
        super(ZoomerAction, self).__init__(panel)
        
    def createWidget(self, parent):
        return Zoomer(self, parent)
    
    def setCurrentIndex(self, index):
        """Called when a user manipulates a Zoomer combobox.
        
        Updates the other widgets and calls the corresponding method of the panel.
        
        """
        for w in self.createdWidgets():
            w.setCurrentIndex(index)
        if index == 0:
            self.parent().fitWidth()
        elif index == 1:
            self.parent().fitHeight()
        elif index == 2:
            self.parent().fitBoth()
        else:
            self.parent().widget().view.zoom(_zoomvalues[index-3] / 100.0)
    
    def updateZoomInfo(self):
        """Connect view.viewModeChanged and layout.scaleChanged to this."""
        import qpopplerview
        mode = self.parent().widget().view.viewMode()
        
        if mode == qpopplerview.FixedScale:
            scale = self.parent().widget().view.scale()
            text = "{0:.0f}%".format(round(scale * 100.0))
            for w in self.createdWidgets():
                w.lineEdit().setText(text)
        else:
            if mode == qpopplerview.FitWidth:
                index = 0
            elif mode == qpopplerview.FitHeight:
                index = 1
            else: # qpopplerview.FitBoth:
                index = 2
            for w in self.createdWidgets():
                w.setCurrentIndex(index)


class Zoomer(QComboBox):
    def __init__(self, action, parent):
        super(Zoomer, self).__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setFocusPolicy(Qt.NoFocus)
        self.setEditable(True)
        self.activated[int].connect(action.setCurrentIndex)
        self.addItems(['']*3)
        self.addItems(list(map("{0}%".format, _zoomvalues)))
        self.setMaxVisibleItems(20)
        app.translateUI(self)
    
    def translateUI(self):
        self.setItemText(0, _("Fit Width"))
        self.setItemText(1, _("Fit Height"))
        self.setItemText(2, _("Fit Page"))
        
