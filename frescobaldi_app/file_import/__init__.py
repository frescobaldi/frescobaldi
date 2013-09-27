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
Import non-lilypond file types. 
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import QAction, QFileDialog, QKeySequence

import app
import actioncollection
import actioncollectionmanager
import plugin
import qutil


class FileImport(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.import_musicxml.triggered.connect(self.importMusicXML)
    
    def importMusicXML(self):
        """ Opens a MusicXML file. Converts it to ly by using musicxml2ly """
        filetypes = app.filetypes('*.xml')
        caption = app.caption(_("dialog title", "Import a MusicXML file"))
        directory = os.path.dirname(self.mainwindow().currentDocument().url().toLocalFile()) or app.basedir()
        importfile = QFileDialog.getOpenFileName(self.mainwindow(), caption, directory, filetypes)
        if not importfile:
            return # the dialog was cancelled by user

        try:
            dlg = self._importDialog
        except AttributeError:
            from . import musicxml
            dlg = self._importDialog = musicxml.Dialog(self.mainwindow())
            dlg.addAction(self.mainwindow().actionCollection.help_whatsthis)
            dlg.setWindowModality(Qt.WindowModal)
        
        dlg.setDocument(importfile)
        if dlg.exec_():
            with qutil.busyCursor():
                stdout, stderr = dlg.run_command()
                print stderr #put this in log window instead
                lyfile = os.path.splitext(importfile)[0] + ".ly"
                self.createDocument(lyfile, stdout.decode('utf-8'))
    
    def createDocument(self, filename, contents):
        """Create a new document using the specified filename and contents.
        
        Make it the current document in our mainwindow and run the engraver.
        
        """
        while os.path.exists(filename) or app.findDocument(QUrl.fromLocalFile(filename)):
            # TODO: find next unique filename
            pass
        doc = app.openUrl(QUrl())
        doc.setPlainText(contents)
        doc.setUrl(QUrl.fromLocalFile(filename))
        doc.setModified(True)
        self.mainwindow().setCurrentDocument(doc)
        import engrave
        engrave.engraver(self.mainwindow()).engrave(True, doc, False)


class Actions(actioncollection.ActionCollection):
    name = "file_import"
    def createActions(self, parent):
        self.import_musicxml = QAction(parent)        
    
    def translateUI(self):
        self.import_musicxml.setText(_("Import MusicXML..."))
        self.import_musicxml.setToolTip(_("Import a MusicXML file using musicxml2ly."))

