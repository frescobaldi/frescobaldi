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
from PyQt4.QtGui import QKeySequence

import app
import panels
import resultfiles


class MusicViewPanel(panels.Panel):
    def __init__(self, mainwindow):
        super(MusicViewPanel, self).__init__(mainwindow)
        #self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+M"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        mainwindow.currentDocumentChanged.connect(self.slotDocumentChanged)
        app.jobFinished.connect(self.setDocument)
        self._previousDocument = lambda: None
        
    def translateUI(self):
        self.setWindowTitle(_("Music View"))
        self.toggleViewAction().setText(_("&Music View"))
    
    def createWidget(self):
        import widget
        return widget.PDFView(self)

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
        if pdfs:
            pdf = pdfs[0]
            self.show()
            self.widget().openPDF(pdf)

