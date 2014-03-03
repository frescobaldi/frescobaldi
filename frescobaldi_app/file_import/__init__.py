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
Import non-lilypond file types.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import QAction, QFileDialog, QKeySequence, QMessageBox, QTextCursor

import app
import actioncollection
import actioncollectionmanager
import plugin
import util
import qutil


class FileImport(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.import_musicxml.triggered.connect(self.importMusicXML)

    def importMusicXML(self):
        """ Opens a MusicXML file. Converts it to ly by using musicxml2ly """
        filetypes = '{0} (*.xml);;{1} (*)'.format(_("XML Files"), _("All Files"))
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
            if stdout: #success
                dlg.saveSettings()
                lyfile = os.path.splitext(importfile)[0] + ".ly"
                doc = self.createDocument(lyfile, stdout.decode('utf-8'))
                self.postImport(dlg.getPostSettings(), doc)
                self.mainwindow().saveDocument(doc)
            else: #failure to convert
                QMessageBox.critical(None, _("Error"),
                    _("The file couldn't be converted. Error message:\n") + stderr.decode('utf-8'))

    def createDocument(self, filename, contents):
        """Create a new document using the specified filename and contents.

        Make it the current document in our mainwindow.

        """
        while os.path.exists(filename) or app.findDocument(QUrl.fromLocalFile(filename)):
            filename = util.next_file(filename)
        doc = app.openUrl(QUrl())
        doc.setPlainText(contents)
        doc.setUrl(QUrl.fromLocalFile(filename))
        doc.setModified(True)
        self.mainwindow().setCurrentDocument(doc)
        return doc       
        
    def postImport(self, settings, doc):
        """Adaptations of the source after running musicxml2ly
		
		Present settings: 
		Reformat source
        Remove superfluous durations
        Remove duration scaling
        Engrave directly
		
        """
        cursor = QTextCursor(doc)		
        if settings[0]:
            import reformat
            reformat.reformat(cursor)
        if settings[1]:
            cursor.select(QTextCursor.Document)
            from rhythm import rhythm
            rhythm.rhythm_implicit_per_line(cursor)
        if settings[2]:
            cursor.select(QTextCursor.Document)
            from rhythm import rhythm
            rhythm.rhythm_remove_fraction_scaling(cursor)       
        if settings[3]:
            import engrave
            engrave.engraver(self.mainwindow()).engrave('preview', doc, False)
        


class Actions(actioncollection.ActionCollection):
    name = "file_import"
    def createActions(self, parent):
        self.import_musicxml = QAction(parent)

    def translateUI(self):
        self.import_musicxml.setText(_("Import MusicXML..."))
        self.import_musicxml.setToolTip(_("Import a MusicXML file using musicxml2ly."))

