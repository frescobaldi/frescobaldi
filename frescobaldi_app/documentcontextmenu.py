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
        app.translateUI(self)
        self.aboutToShow.connect(self.updateActions)
    
    def createActions(self):
        self.doc_save = self.addAction(icons.get('document-save'), '')
        self.doc_save_as = self.addAction(icons.get('document-save-as'), '')
        self.addSeparator()
        self.doc_close = self.addAction(icons.get('document-close'), '')
        self.doc_close_others = self.addAction(icons.get('document-close'), '')
        self.addSeparator()
        self.doc_toggle_sticky = self.addAction(icons.get('pushpin'), '')
        self.doc_toggle_sticky.setCheckable(True)
        
        self.doc_save.triggered.connect(self.docSave)
        self.doc_save_as.triggered.connect(self.docSaveAs)
        self.doc_close.triggered.connect(self.docClose)
        self.doc_close_others.triggered.connect(self.docCloseOther)
        self.doc_toggle_sticky.triggered.connect(self.docToggleSticky)
    
    def updateActions(self):
        """Called just before show."""
        doc = self._doc()
        if doc:
            import engrave
            engraver = engrave.Engraver.instance(self.mainwindow())
            self.doc_toggle_sticky.setChecked(doc is engraver.stickyDocument())
    
    def translateUI(self):
        self.doc_save.setText(_("&Save"))
        self.doc_save_as.setText(_("Save &As..."))
        self.doc_close.setText(_("&Close"))
        self.doc_close_others.setText(_("Close Other Documents"))
        self.doc_toggle_sticky.setText(_("Always &Engrave This Document"))
    
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

    def docCloseOther(self):
        """ Closes all documents that are not our current document. """
        cur = self._doc()
        if not cur:
            return # not clear which to keep open...
        win = self.mainwindow()
        win.setCurrentDocument(cur, findOpenView=True)
        win.closeOtherDocuments()

    def docToggleSticky(self):
        doc = self._doc()
        if doc:
            import engrave
            engraver = engrave.Engraver.instance(self.mainwindow())
            if doc is engraver.stickyDocument():
                engraver.setStickyDocument(None)
            else:
                engraver.setStickyDocument(doc)


