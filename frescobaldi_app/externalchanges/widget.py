# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
This is the window displayed when a Document is modified by an external program.

For files that are deleted (or moved elsewhere, this can't be distinguished)
the options are:
  - save the document back again ("it was removed accidentally")
  - close document ("it can be discarded anyway")

For files that are overwritten and now have different contents:
  - reload the document from disk (undoable)
  - show a diff
  - save the document back again ("it got overwritten accidentally")
  - close document ("it is not needed anyway")
  
  
"""

from __future__ import unicode_literals


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import qutil
import widgets.dialog
import documentwatcher
import help


def window():
    global _window
    try:
        return _window
    except NameError:
        _window = ChangedDocumentsListDialog()
    return _window


class ChangedDocumentsListDialog(widgets.dialog.Dialog):
    def __init__(self):
        super(ChangedDocumentsListDialog, self).__init__(buttons=('close',))
        self.setWindowModality(Qt.NonModal)
        
        layout = QGridLayout(margin=0)
        self.mainWidget().setLayout(layout)
        self.tree = QTreeWidget(headerHidden=True)
        
        self.buttonReload = QPushButton()
        self.buttonReloadAll = QPushButton()
        self.buttonSave = QPushButton()
        self.buttonSaveAll = QPushButton()
        self.buttonClose = QPushButton()
        self.buttonCloseAll = QPushButton()
        self.buttonShowDiff = QPushButton()
        
        layout.addWidget(self.tree, 0, 0, 7, 1)
        layout.addWidget(self.buttonReload, 0, 1)
        layout.addWidget(self.buttonReloadAll, 1, 1)
        layout.addWidget(self.buttonSave, 2, 1)
        layout.addWidget(self.buttonSaveAll, 3, 1)
        layout.addWidget(self.buttonClose, 4, 1)
        layout.addWidget(self.buttonCloseAll, 5, 1)
        layout.addWidget(self.buttonShowDiff, 6, 1)
        app.documentClosed.connect(self.removeDocument)
        app.documentSaved.connect(self.removeDocument)
        app.documentUrlChanged.connect(self.removeDocument)
        app.documentLoaded.connect(self.removeDocument)
    
        app.translateUI(self)
        qutil.saveDialogSize(self, 'changed_documents', QSize(400, 200))
        help.addButton(self.buttonBox(), "help_external_changes")
        self.button('close').setFocus()
    
    def translateUI(self):
        self.setWindowTitle(app.caption(_("Modified Files")))
        self.setMessage(_(
            "The following files were overwritten or deleted by other "
            "applications:"))
        self.buttonReload.setText(_("Reload"))
        self.buttonReload.setToolTip(_(
            "Reloads the selected documents from disk. "
            "(You can still reach the previous state of the document "
            "using the Undo command.)"))
        self.buttonReloadAll.setText(_("Reload All"))
        self.buttonReloadAll.setToolTip(_(
            "Reloads all externally modified documents from disk. "
            "(You can still reach the previous state of the document "
            "using the Undo command.)"))
        self.buttonSave.setText(_("Save"))
        self.buttonSave.setToolTip(_(
            "Saves the selected documents to disk, overwriting the "
            "modifications by another program."))
        self.buttonSaveAll.setText(_("Save All"))
        self.buttonSaveAll.setToolTip(_(
            "Saves all documents to disk, overwriting the modifications by "
            "another program."))
        self.buttonClose.setText(_("Close"))
        self.buttonClose.setToolTip(_(
            "Closes the selected documents, discarding our version of the "
            "document's contents."))
        self.buttonCloseAll.setText(_("Close All"))
        self.buttonCloseAll.setToolTip(_(
            "Closes all documents, discarding our version of the "
            "document's contents."))
        self.buttonShowDiff.setText(_("Show Difference..."))
        self.buttonShowDiff.setToolTip(_(
            "Shows the differences between the current document "
            "and the file on disk."))
    
    def setDocuments(self, documents):
        """Display the specified documents in the list."""
    
    def removeDocument(self, document):
        """Remove the specified document from our list."""


