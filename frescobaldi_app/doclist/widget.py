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
The documents list tool widget.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons
import jobmanager


class Widget(QTreeWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool, headerHidden=True)
        
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentLoaded.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.jobStarted.connect(self.setDocumentStatus)
        app.jobFinished.connect(self.setDocumentStatus)
       
        tool.mainwindow().currentDocumentChanged.connect(self.selectDocument)

        # add all existing docs to the list
        self._items = {}
        for d in app.documents:
            self.addDocument(d)
        
        self.currentItemChanged.connect(self.slotItemActivated)
            
    def addDocument(self, doc):
        self._items[doc] = QTreeWidgetItem(self)
        self.setDocumentStatus(doc)
    
    def removeDocument(self, doc):
        i = self._items.pop(doc)
        self.takeTopLevelItem(self.indexOfTopLevelItem(i))
        self.sortItems(0, Qt.AscendingOrder)

    def selectDocument(self, doc):
        self.setCurrentItem(self._items[doc])

    def setDocumentStatus(self, doc):
        i = self._items[doc]
        i.setText(0, doc.documentName())
        # icon
        if jobmanager.isRunning(doc):
            icon = 'lilypond-run'
        elif doc.isModified():
            icon = 'document-save'
        else:
            icon = 'text-plain'
        i.setIcon(0, icons.get(icon))
        self.sortItems(0, Qt.AscendingOrder)
    
    def slotItemActivated(self, item):
        for d, i in self._items.items():
            if i == item:
                self.parentWidget().mainwindow().setCurrentDocument(d)
                break


