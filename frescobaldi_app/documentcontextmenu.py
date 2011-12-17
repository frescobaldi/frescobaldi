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
A context menu with actions for a Document.
Used by the tabbar and the doclist tool.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtGui import QMenu

import app
import icons


class DocumentContextMenu(QMenu):
    def __init__(self, mainwindow):
        super(DocumentContextMenu, self).__init__(mainwindow)
        self._doc = lambda: None
        
        self.createActions()
        app.languageChanged.connect(self.translateUI)
        self.translateUI()
    
    def createActions(self):
        self.doc_save = self.addAction(icons.get('document-save'), '')
        self.doc_save_as = self.addAction(icons.get('document-save-as'), '')
        self.addSeparator()
        self.doc_close = self.addAction(icons.get('document-close'), '')
        
        self.doc_save.triggered.connect(self.docSave)
        self.doc_save_as.triggered.connect(self.docSaveAs)
        self.doc_close.triggered.connect(self.docClose)
    
    def translateUI(self):
        self.doc_save.setText(_("&Save"))
        self.doc_save_as.setText(_("Save &As..."))
        self.doc_close.setText(_("&Close"))
    
    def mainwindow(self):
        return self.parentWidget()
        
    def exec_(self, document, pos):
        self._doc = weakref.ref(document)
        super(DocumentContextMenu, self).exec_(pos)
    
    def docSave(self):
        doc = self._doc()
        if doc:
            self.mainwindow().saveDocument(doc)
    
    def docSaveAs(self):
        doc = self._doc()
        if doc:
            self.mainwindow().saveDocumentAs(doc)
    
    def docClose(self):
        doc = self._doc()
        if doc:
            self.mainwindow().closeDocument(doc)


