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
        self.setAlternatingRowColors(True)
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentLoaded.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.jobStarted.connect(self.setDocumentStatus)
        app.jobFinished.connect(self.setDocumentStatus)
        tool.mainwindow().currentDocumentChanged.connect(self.selectDocument)
        self.currentItemChanged.connect(self.slotItemActivated)
        app.settingsChanged.connect(self.populate)
        self.populate()
    
    def populate(self):
        self._group = QSettings().value(
            "document_list/group_by_folder", False) in (True, "true")
        self.setRootIsDecorated(not self._group)
        self.clear()
        self._paths = {}
        self._items = {}
        with util.signalsBlocked(self):
            # add all existing docs to the list
            for d in app.documents:
                self.addDocument(d)
            doc = self.parentWidget().mainwindow().currentDocument()
            if doc:
                self.selectDocument(doc)
        
    def addDocument(self, doc):
        self._items[doc] = QTreeWidgetItem(self)
        self.setDocumentStatus(doc)
    
    def removeDocument(self, doc):
        i = self._items.pop(doc)
        if not self._group:
            self.takeTopLevelItem(self.indexOfTopLevelItem(i))
            return
        parent = i.parent()
        parent.takeChild(parent.indexOfChild(i))
        if parent.childCount() == 0:
            self.takeTopLevelItem(self.indexOfTopLevelItem(parent))
            del self._paths[parent._path]
    
    def selectDocument(self, doc):
        self.setCurrentItem(self._items[doc])

    def setDocumentStatus(self, doc):
        i = self._items[doc]
        # set properties according to document
        i.setText(0, doc.documentName())
        if jobmanager.isRunning(doc):
            icon = 'lilypond-run'
        elif doc.isModified():
            icon = 'document-save'
        else:
            icon = 'text-plain'
        i.setIcon(0, icons.get(icon))
        i.setToolTip(0, path(doc.url()))
        # handle ordering in groups if desired
        if self._group:
            self.groupDocument(doc)
        else:
            self.sortItems(0, Qt.AscendingOrder)
    
    def groupDocument(self, doc):
        """Called, if grouping is enabled, to group the document."""
        i = self._items[doc]
        p = path(doc.url())
        new_parent = self._paths.get(p)
        if new_parent is None:
            new_parent = self._paths[p] = QTreeWidgetItem(self)
            new_parent._path = p
            new_parent.setText(0, p or _("Untitled"))
            new_parent.setIcon(0, icons.get("folder-open"))
            new_parent.setFlags(Qt.ItemIsEnabled)
            new_parent.setExpanded(True)
            self.sortItems(0, Qt.AscendingOrder)
        old_parent = i.parent()
        if old_parent == new_parent:
            return
        if old_parent:
            old_parent.takeChild(old_parent.indexOfChild(i))
            if old_parent.childCount() == 0:
                self.takeTopLevelItem(self.indexOfTopLevelItem(old_parent))
                del self._paths[old_parent._path]
        else:
            self.takeTopLevelItem(self.indexOfTopLevelItem(i))
        new_parent.addChild(i)
        new_parent.sortChildren(0, Qt.AscendingOrder)
    
    def document(self, item):
        """Returns the document for item."""
        for d, i in self._items.items():
            if i == item:
                return d
        
    def slotItemActivated(self, item):
        doc = self.document(item)
        if doc:
            self.parentWidget().mainwindow().setCurrentDocument(doc)
    
    def contextMenuEvent(self, ev):
        item = self.itemAt(ev.pos())
        if item:
            doc = self.document(item)
            if doc:
                import documentcontextmenu
                mainwindow = self.parentWidget().mainwindow()
                menu = documentcontextmenu.DocumentContextMenu(mainwindow)
                menu.exec_(doc, ev.globalPos())
                menu.deleteLater()


