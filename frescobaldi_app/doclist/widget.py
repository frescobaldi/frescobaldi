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

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import util
import icons
import jobmanager


def path(url):
    """Returns the path, as a string, of the url to group documents.
    
    Returns None if the document is nameless.
    
    """
    if url.isEmpty():
        return None
    elif url.toLocalFile():
        return util.homify(os.path.dirname(url.toLocalFile()))
    else:
        return url.resolved(QUrl('.')).toString(QUrl.RemoveUserInfo)


class Widget(QTreeWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool, headerHidden=True)
        self._paths = {}
        self._items = {}
        
        self.readSettings()
        app.settingsChanged.connect(self.readSettingsAgain)
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentLoaded.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.jobStarted.connect(self.setDocumentStatus)
        app.jobFinished.connect(self.setDocumentStatus)
       
        tool.mainwindow().currentDocumentChanged.connect(self.selectDocument)
        
        # add all existing docs to the list
        for d in app.documents:
            self.addDocument(d)
        doc = tool.mainwindow().currentDocument()
        if doc:
            self.selectDocument(doc)
        self.currentItemChanged.connect(self.slotItemActivated)
	
    def readSettings(self):
        self._group = QSettings().value(
            "document_list/group_by_folder", False) in (True, "true")
    
    def readSettingsAgain(self):
        self.readSettings()
        
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
        i.setToolTip(0, path(doc.url()))
        self.sortItems(0, Qt.AscendingOrder)
    
    def slotItemActivated(self, item):
        for d, i in self._items.items():
            if i == item:
                self.parentWidget().mainwindow().setCurrentDocument(d)
                break


