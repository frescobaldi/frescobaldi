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
import importlib
import shutil

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QTextCursor
from PyQt6.QtWidgets import QFileDialog, QMessageBox

import app
import icons
import actioncollection
import actioncollectionmanager
import plugin
import util
import job.dialog


class FileImport(plugin.MainWindowPlugin):

    def __init__(self, mainwindow):
        self._import_job = None
        self._import_dialog = None
        self._import_file = ''
        self._mxml_dialog = None
        self._midi_dlg = None
        self._abc_dlg = None
        self.targets = {
            '.xml': ('.musicxml', self._mxml_dialog),
            '.musicxml': ('.musicxml', self._mxml_dialog),
            '.mxl': ('.musicxml', self._mxml_dialog),
            '.midi': ('.midi', self._midi_dlg),
            '.mid': ('.midi', self._midi_dlg),
            '.abc': ('.abc', self._abc_dlg)
        }

        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.import_any.triggered.connect(self.import_any)
        ac.import_musicxml.triggered.connect(self.import_musicxml)
        ac.import_midi.triggered.connect(self.import_midi)
        ac.import_abc.triggered.connect(self.import_abc)

    def configure_import(self, input_file):
        """Open the configuration dialog corresponding to the file type."""
        self._import_file = input_file

        # Retrieve module and dialog corresponding to import file type
        ext = os.path.splitext(self._import_file)[1]
        module_name, dlg = self.targets[ext]
        if not dlg:
            # create dialog suitable for import file type
            module = importlib.import_module(module_name, 'file_import')
            dlg = module.Dialog(self.mainwindow())
        dlg.set_input(self._import_file)
        self._import_dialog = dlg

    def do_import(self, filetypes, caption, multiple=False):
        """Control structure for file import.
        Can either import "any" file(s) or one file of a specific file type.
        """
        self._import_files = self.get_import_file(filetypes, caption, multiple)
        for filename in self._import_files:
            # TODO: Update the file dialog to not allow "All files" anymore
            # (probably requires the use of a QSortFilterProxyModel).
            # Then is_importable and the following conditional can be
            # removed.
            if self.is_importable(filename):
                self.configure_import(filename)
                self.run_import()
            else:
                QMessageBox.critical(None, _("Error"),
                    _("The file {filename} could not be converted: "
                      "wrong file type.").format(filename=filename))

    def get_import_file(self, filetypes, caption, multiple=False):
        """Open a File Open dialog for the requested filetype(s),
        return a list with one or multiple existing file names
        or an empty list in case the user has canceled the dialog."""
        caption = app.caption(caption)
        directory = (os.path.dirname(
            self.mainwindow().currentDocument().url().toLocalFile())
            or app.basedir())

        if multiple:
            result = QFileDialog.getOpenFileNames(
                self.mainwindow(), caption, directory, filetypes)[0]
            return result if result else []
        else:
            result = QFileDialog.getOpenFileName(
                self.mainwindow(), caption, directory, filetypes)[0]
            return [result] if result else []

    def import_any(self):
        """Reads the file type and determines which import to use."""
        filetypes = ';;'.join((
            '{} (*.xml *.musicxml *.mxl *.midi *.mid *.abc)'.format(_("All importable formats")),
            '{} (*.xml *.musicxml *.mxl)'.format(_("MusicXML Files")),
            '{} (*.midi *.mid)'.format(_("Midi Files")),
            '{} (*.abc)'.format(_("ABC Files")),
            '{} (*)'.format(_("All Files")),
        ))
        caption = app.caption(_("dialog title", "Import"))
        self.do_import(filetypes, caption, multiple=True)

    def import_musicxml(self):
        """Opens a MusicXML file. Converts it to ly by using musicxml2ly."""
        filetypes = '{} (*.xml *.musicxml *.mxl);;{} (*)'.format(
            _("MusicXML Files"), _("All Files"))
        caption = _("dialog title", "Import a MusicXML file")
        self.do_import(filetypes, caption)

    def import_midi(self):
        """Opens an midi file. Converts it to ly by using midi2ly."""
        filetypes = '{} (*.midi *.mid);;{} (*)'.format(
            _("Midi Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import a midi file"))
        self.do_import(filetypes, caption)

    def import_abc(self):
        """Opens an abc file. Converts it to ly by using abc2ly."""
        filetypes = '{} (*.abc);;{} (*)'.format(
            _("ABC Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import an abc file"))
        self.do_import(filetypes, caption)

    def import_done(self):
        j = self._import_job
        conf_dlg = self._import_dialog
        conf_dlg.saveSettings()
        lyfile = os.path.splitext(self._import_file)[0] + ".ly"
        while (os.path.exists(lyfile)
            or app.findDocument(QUrl.fromLocalFile(lyfile))):
            lyfile = util.next_file(lyfile)
        shutil.move(j.output_file(), lyfile)

        doc = app.openUrl(QUrl.fromLocalFile(lyfile))
        doc.setModified(True)
        self.mainwindow().setCurrentDocument(doc)

        self.post_import(conf_dlg.get_post_settings(), doc)
        self.mainwindow().saveDocument(doc)

    def is_importable(self, filename):
        """Check if the file is importable."""
        ext = os.path.splitext(filename)[1]
        return ext in ['.xml', '.musicxml', '.mxl', '.midi', '.mid', '.abc']

    def post_import(self, settings, doc):
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
            cursor.select(QTextCursor.SelectionType.Document)
            from rhythm import rhythm
            rhythm.rhythm_implicit_per_line(cursor)
        if settings[2]:
            cursor.select(QTextCursor.SelectionType.Document)
            from rhythm import rhythm
            rhythm.rhythm_remove_fraction_scaling(cursor)
        if settings[3]:
            import engrave
            engrave.engraver(self.mainwindow()).engrave('preview', doc, False)

    def run_import(self):
        """Generic execution of all import dialogs."""
        conf_dlg = self._import_dialog
        if conf_dlg.exec():
            self._import_job = j = conf_dlg.job()
            dlg = job.dialog.Dialog(self.mainwindow(), auto_accept=True)
            dlg.accepted.connect(self.import_done)
            dlg.run(j)


class Actions(actioncollection.ActionCollection):
    name = "file_import"
    def createActions(self, parent):
        self.import_any = QAction(parent)
        self.import_musicxml = QAction(parent)
        self.import_midi = QAction(parent)
        self.import_abc = QAction(parent)

        self.import_any.setIcon(icons.get("document-import"))

    def translateUI(self):
        self.import_any.setText(_("Import..."))
        self.import_any.setToolTip(_("Generic import for all LilyPond tools."))
        self.import_musicxml.setText(_("Import MusicXML..."))
        self.import_musicxml.setToolTip(_("Import a MusicXML file using musicxml2ly."))
        self.import_midi.setText(_("Import Midi..."))
        self.import_midi.setToolTip(_("Import a Midi file using midi2ly."))
        self.import_abc.setText(_("Import abc..."))
        self.import_abc.setToolTip(_("Import an abc file using abc2ly."))
