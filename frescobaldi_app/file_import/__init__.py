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


import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QKeySequence, QTextCursor
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox

import app
import icons
import actioncollection
import actioncollectionmanager
import plugin
import util
import qutil


class FileImport(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.import_all.triggered.connect(self.importAll)
        ac.import_musicxml.triggered.connect(self.importMusicXML)
        ac.import_midi.triggered.connect(self.importMidi)
        ac.import_abc.triggered.connect(self.importAbc)

    def importAll(self):
        """Reads the file type and determines which import to use."""
        filetypes = ';;'.join((
            '{0} (*.xml *.mxl *.midi *.mid *.abc)'.format(_("All importable formats")),
            '{0} (*.xml *.mxl)'.format(_("MusicXML Files")),
            '{0} (*.midi *.mid)'.format(_("Midi Files")),
            '{0} (*.abc)'.format(_("ABC Files")),
            '{0} (*)'.format(_("All Files")),
        ))
        caption = app.caption(_("dialog title", "Import"))
        directory = os.path.dirname(self.mainwindow().currentDocument().url().toLocalFile()) or app.basedir()
        importfiles = QFileDialog.getOpenFileNames(self.mainwindow(), caption, directory, filetypes)[0]
        if not importfiles:
            return # the dialog was cancelled by user
        for imp in importfiles:
            if self.isImportable(imp):
                self.openDialog(imp)
            else:
                QMessageBox.critical(None, _("Error"),
                    _("The file {filename} could not be converted. "
                      "Wrong file type.").format(filename=imp))

    def isImportable(self, infile):
        """Check if the file is importable."""
        ext = os.path.splitext(infile)[1]
        if ext in ['.xml', '.mxl', '.midi', '.mid', '.abc']:
            return True
        else:
            return False

    def openDialog(self, infile):
        """Check file type and open the proper dialog."""
        self.importfile = infile
        ext = os.path.splitext(infile)[1]
        if ext == '.xml' or ext == '.mxl':
            self.openMusicxmlDialog()
        elif ext == '.midi' or ext == '.mid':
            self.openMidiDialog()
        elif ext == '.abc':
            self.openAbcDialog()

    def importMusicXML(self):
        """Opens a MusicXML file. Converts it to ly by using musicxml2ly."""
        filetypes = '{0} (*.xml *.mxl);;{1} (*)'.format(
            _("MusicXML Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import a MusicXML file"))
        directory = os.path.dirname(self.mainwindow().currentDocument().url().toLocalFile()) or app.basedir()
        self.importfile = QFileDialog.getOpenFileName(self.mainwindow(), caption, directory, filetypes)[0]
        if not self.importfile:
            return # the dialog was cancelled by user
        self.openMusicxmlDialog()

    def openMusicxmlDialog(self):
        try:
            dlg = self._importDialog = self.mxmlDlg
        except AttributeError:
            from . import musicxml
            dlg = self._importDialog = self.mxmlDlg = musicxml.Dialog(self.mainwindow())
            dlg.addAction(self.mainwindow().actionCollection.help_whatsthis)
            dlg.setWindowModality(Qt.WindowModal)
        self.runImport()

    def importMidi(self):
        """Opens an midi file. Converts it to ly by using midi2ly."""
        filetypes = '{0} (*.midi *.mid);;{1} (*)'.format(
            _("Midi Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import a midi file"))
        directory = os.path.dirname(self.mainwindow().currentDocument().url().toLocalFile()) or app.basedir()
        self.importfile = QFileDialog.getOpenFileName(self.mainwindow(), caption, directory, filetypes)[0]
        if not self.importfile:
            return # the dialog was cancelled by user
        self.openMidiDialog()

    def openMidiDialog(self):
        try:
            dlg = self._importDialog = self.midDlg
        except AttributeError:
            from . import midi
            dlg = self._importDialog = self.midDlg = midi.Dialog(self.mainwindow())
            dlg.addAction(self.mainwindow().actionCollection.help_whatsthis)
            dlg.setWindowModality(Qt.WindowModal)
        self.runImport()

    def importAbc(self):
        """Opens an abc file. Converts it to ly by using abc2ly."""
        filetypes = '{0} (*.abc);;{1} (*)'.format(
            _("ABC Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import an abc file"))
        directory = os.path.dirname(self.mainwindow().currentDocument().url().toLocalFile()) or app.basedir()
        self.importfile = QFileDialog.getOpenFileName(self.mainwindow(), caption, directory, filetypes)[0]
        if not self.importfile:
            return # the dialog was cancelled by user
        self.openAbcDialog()

    def openAbcDialog(self):
        try:
            dlg = self._importDialog = self.abcDlg
        except AttributeError:
            from . import abc
            dlg = self._importDialog = self.abcDlg = abc.Dialog(self.mainwindow())
            dlg.addAction(self.mainwindow().actionCollection.help_whatsthis)
            dlg.setWindowModality(Qt.WindowModal)
        self.runImport()

    def runImport(self):
        """Generic execution of all import dialogs."""
        dlg = self._importDialog
        dlg.setDocument(self.importfile)
        if dlg.exec_():
            with qutil.busyCursor():
                stdout, stderr = dlg.run_command()
            if stdout: #success
                dlg.saveSettings()
                lyfile = os.path.splitext(self.importfile)[0] + ".ly"
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
        self.import_all = QAction(parent)
        self.import_musicxml = QAction(parent)
        self.import_midi = QAction(parent)
        self.import_abc = QAction(parent)

        self.import_all.setIcon(icons.get("document-import"))

    def translateUI(self):
        self.import_all.setText(_("Import..."))
        self.import_all.setToolTip(_("Generic import for all LilyPond tools."))
        self.import_musicxml.setText(_("Import MusicXML..."))
        self.import_musicxml.setToolTip(_("Import a MusicXML file using musicxml2ly."))
        self.import_midi.setText(_("Import Midi..."))
        self.import_midi.setToolTip(_("Import a Midi file using midi2ly."))
        self.import_abc.setText(_("Import abc..."))
        self.import_abc.setToolTip(_("Import an abc file using abc2ly."))

