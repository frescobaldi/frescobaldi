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
Export to non-lilypond file types. 
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import QAction, QFileDialog, QKeySequence, QMessageBox 

import app
import actioncollection
import actioncollectionmanager
import document
import plugin
import util
import qutil


class FileExport(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.export_musicxml.triggered.connect(self.exportMusicXML)
    
    def exportMusicXML(self):
        """ Convert the current document to MusicXML """
        doc = self.mainwindow().currentDocument()
        orgname = doc.url().toLocalFile()
        namelist = orgname.split('.')
        filename = namelist[0]+'.xml'
        import source2musxml
        musxmlparser = source2musxml.parse_source(doc)
        xmldoc = app.openUrl(QUrl())
        xmldoc.setPlainText(musxmlparser.output())
        filetypes = app.filetypes('*.xml')
        self.saveDocumentAs(xmldoc, filename, filetypes) 
        
    def saveDocumentAs(self, doc, filename, filetypes):
        """ Saves the document, always asking for a name.
        
        Returns True if saving succeeded.
        
        """
        caption = app.caption(_("dialog title", "Save File"))
        filename = QFileDialog.getSaveFileName(self.mainwindow(), caption, filename, filetypes)
        if not filename:
            return False # cancelled
        if not util.iswritable(filename):
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}").format(url=filename))
            return False
        url = QUrl.fromLocalFile(filename)
        doc.setUrl(url)
        return self.saveDocument(doc)
        
    def saveDocument(self, doc):
        """ Saves the document, asking for a name if necessary.
        
        Returns True if saving succeeded.
        
        """
        if doc.url().isEmpty():
            return self.saveDocumentAs(doc)
        filename = dest = doc.url().toLocalFile()
        if not filename:
            dest = doc.url().toString()
        if not util.iswritable(filename):
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}").format(url=dest))
            return False
        success = doc.save()
        if not success:
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}").format(url=filename))
        return success    


class Actions(actioncollection.ActionCollection):
    name = "file_export"
    def createActions(self, parent):
        self.export_musicxml = QAction(parent)        
    
    def translateUI(self):
        self.export_musicxml.setText(_("Export MusicXML..."))
        self.export_musicxml.setToolTip(_("Export current document as MusicXML."))

