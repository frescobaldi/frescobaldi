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

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction, QComboBox, QKeySequence, QWidgetAction

import app
import actioncollection
import actioncollectionmanager
import icons
import panels
import resultfiles


class MusicViewPanel(panels.Panel):
    def __init__(self, mainwindow):
        super(MusicViewPanel, self).__init__(mainwindow)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+M"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        mainwindow.currentDocumentChanged.connect(self.slotDocumentChanged)
        app.jobFinished.connect(self.setDocument)
        self._previousDocument = lambda: None
        
        ac = self.actionCollection = Actions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.music_print.triggered.connect(self.printMusic)
        ac.music_zoom_in.triggered.connect(self.zoomIn)
        ac.music_zoom_out.triggered.connect(self.zoomOut)
        ac.music_fit_width.triggered.connect(self.fitWidth)
        ac.music_fit_height.triggered.connect(self.fitHeight)
        ac.music_fit_both.triggered.connect(self.fitBoth)
    
    def translateUI(self):
        self.setWindowTitle(_("Music View"))
        self.toggleViewAction().setText(_("&Music View"))
    
    def createWidget(self):
        import widget
        m = widget.MusicView(self)
        m.view.viewModeChanged.connect(self.slotViewModeChanged)
        return m
        
    def slotViewModeChanged(self, viewmode):
        import qpopplerview
        ac = self.actionCollection
        ac.music_fit_width.setChecked(viewmode == qpopplerview.FitWidth)
        ac.music_fit_height.setChecked(viewmode == qpopplerview.FitHeight)
        ac.music_fit_both.setChecked(viewmode == qpopplerview.FitBoth)

    def slotDocumentChanged(self, document):
        prev = self._previousDocument()
        if prev:
            prev.loaded.disconnect(self.setDocument)
        document.loaded.connect(self.setDocument)
        self._previousDocument = weakref.ref(document)
        self.setDocument(document)
        
    def setDocument(self, document=None):
        if document is None:
            document = self.mainwindow().currentDocument()
        # TEMP!!
        pdfs = resultfiles.results(document).files(".pdf")
        self.actionCollection.music_document_select.setPDFs(pdfs)
        if pdfs:
            pdf = pdfs[0]
            self.show()
            self.widget().openPDF(pdf)
        ac = self.actionCollection
        ac.music_document_select.setEnabled(bool(pdfs))
        ac.music_print.setEnabled(bool(pdfs))
        
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
        
        self.music_print.setShortcuts(QKeySequence.Print)
        self.music_zoom_in.setShortcuts(QKeySequence.ZoomIn)
        self.music_zoom_out.setShortcuts(QKeySequence.ZoomOut)
        
    def translateUI(self):
        self.music_print.setText(_("&Print Music..."))
        self.music_zoom_in.setText(_("Zoom &In"))
        self.music_zoom_out.setText(_("Zoom &Out"))
        self.music_fit_width.setText(_("Fit &Width"))
        self.music_fit_height.setText(_("Fit &Height"))
        self.music_fit_both.setText(_("Fit &Page"))
        

class DocumentChooserAction(QWidgetAction):
    def __init__(self, panel):
        super(DocumentChooserAction, self).__init__(panel)
        
    def createWidget(self, parent):
        return DocumentChooser(self.parent(), parent)
        
    def setPDFs(self, pdfs):
        for w in self.createdWidgets():
            w.clear()
            w.addItems(map(os.path.basename, pdfs))
            

class DocumentChooser(QComboBox):
    def __init__(self, panel, parent):
        super(DocumentChooser, self).__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        app.translateUI(self)
        
    def translateUI(self):
        self.setToolTip(_("Choose the PDF document to display."))

