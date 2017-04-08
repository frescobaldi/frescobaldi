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
The documents list tool widget.
"""


import os

from PyQt5.QtCore import QItemSelectionModel, QSettings, Qt, QUrl
from PyQt5.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem

import app
import util
import qutil
import icons
import documenticon
import engrave


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
        self.setRootIsDecorated(False)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentLoaded.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.jobStarted.connect(self.setDocumentStatus)
        app.jobFinished.connect(self.setDocumentStatus)
        engraver = engrave.Engraver.instance(tool.mainwindow())
        engraver.stickyChanged.connect(self.setDocumentStatus)
        tool.mainwindow().currentDocumentChanged.connect(self.selectDocument)
        self.itemSelectionChanged.connect(self.slotItemSelectionChanged)
        app.settingsChanged.connect(self.populate)
        self.populate()

    def populate(self):
        self._group = QSettings().value("document_list/group_by_folder", False, bool)
        self.clear()
        self._paths = {}
        self._items = {}
        with qutil.signalsBlocked(self):
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
        self.setCurrentItem(self._items[doc], 0, QItemSelectionModel.ClearAndSelect)

    def setDocumentStatus(self, doc):
        try:
            i = self._items[doc]
        except KeyError:
            # this fails when a document is closed that had a job running,
            # in that case setDocumentStatus is called twice (the second time
            # when the job quits, but then we already removed the document)
            return
        # set properties according to document
        i.setText(0, doc.documentName())
        i.setIcon(0, documenticon.icon(doc, self.parentWidget().mainwindow()))
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

    def slotItemSelectionChanged(self):
        if len(self.selectedItems()) == 1:
            doc = self.document(self.selectedItems()[0])
            if doc:
                self.parentWidget().mainwindow().setCurrentDocument(doc)

    def contextMenuEvent(self, ev):
        item = self.itemAt(ev.pos())
        if not item:
            return

        mainwindow = self.parentWidget().mainwindow()

        selection = self.selectedItems()
        doc = self.document(item)

        if len(selection) <= 1 and doc:
            # a single document is right-clicked
            import documentcontextmenu
            menu = documentcontextmenu.DocumentContextMenu(mainwindow)
            menu.exec_(doc, ev.globalPos())
            menu.deleteLater()
            return

        menu = QMenu(mainwindow)
        save = menu.addAction(icons.get('document-save'), '')
        menu.addSeparator()
        close = menu.addAction(icons.get('document-close'), '')

        if len(selection) > 1:
            # multiple documents are selected
            save.setText(_("Save selected documents"))
            close.setText(_("Close selected documents"))
            documents = [self.document(item) for item in selection]
        else:
            documents = [self.document(item.child(i)) for i in range(item.childCount())]
            if item._path:
                # a directory item is right-clicked
                save.setText(_("Save documents in this folder"))
                close.setText(_("Close documents in this folder"))
            else:
                # the "Untitled" group is right-clicked
                save.setText(_("Save all untitled documents"))
                close.setText(_("Close all untitled documents"))

        @save.triggered.connect
        def savedocuments():
            for d in documents:
                if d.url().isEmpty() or d.isModified():
                    mainwindow.setCurrentDocument(d)
                if not mainwindow.saveDocument(d):
                    break

        @close.triggered.connect
        def close_documents():
            for d in documents:
                if not mainwindow.closeDocument(d):
                    break

        menu.exec_(ev.globalPos())
        menu.deleteLater()


