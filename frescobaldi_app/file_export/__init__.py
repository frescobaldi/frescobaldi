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
Export to non-lilypond file types.
"""


import os

from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox

import app
import icons
import actioncollection
import actioncollectionmanager
import documentinfo
import plugin
import tokeniter
import appinfo
import codecs
import job
import qutil
import resultfiles
import externalcommand


class FileExport(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.export_musicxml.triggered.connect(self.exportMusicXML)
        ac.export_audio.triggered.connect(self.exportAudio)

    def exportMusicXML(self):
        """ Convert the current document to MusicXML """
        doc = self.mainwindow().currentDocument()
        orgname = doc.url().toLocalFile()
        filename = os.path.splitext(orgname)[0] + '.xml'
        caption = app.caption(_("dialog title", "Export MusicXML File"))
        filetypes = '{0} (*.xml);;{1} (*)'.format(_("XML Files"), _("All Files"))
        filename = QFileDialog.getSaveFileName(self.mainwindow(), caption, filename, filetypes)[0]
        if not filename:
            return False # cancelled
        import ly.musicxml
        writer = ly.musicxml.writer()
        writer.parse_text(doc.toPlainText(), orgname)
        xml = writer.musicxml()
        # put the Frescobaldi version in the xml file
        software = xml.root.find('.//encoding/software')
        software.text = "{0} {1}".format(appinfo.appname, appinfo.version)
        try:
            xml.write(filename)
        except (IOError, OSError) as err:
            QMessageBox.warning(self.mainwindow(), app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}\n\n{error}").format(
                    url=filename, error=err.strerror))

    def exportAudio(self):
        """ Convert the current document to Audio """
        mainwin = self.mainwindow()
        doc = mainwin.currentDocument()
        midfiles = resultfiles.results(doc).files('.mid*')
        if not midfiles:
            QMessageBox.critical(None, _("Error"),
                    _("The audio file couldn't be created. Please create midi file first"))
            return False
        orgname = doc.url().toLocalFile()
        midifile = midfiles[0]
        wavfile = os.path.splitext(orgname)[0] + '.wav'
        caption = app.caption(_("dialog title", "Export Audio File"))
        filetypes = '{0} (*.wav);;{1} (*)'.format(_("WAV Files"), _("All Files"))
        wavfile = QFileDialog.getSaveFileName(mainwin, caption, wavfile, filetypes)[0]
        if not wavfile:
            return False # cancelled
        dlg = AudioExportDialog(mainwin, caption)
        dlg.setAttribute(Qt.WA_DeleteOnClose) # we use it only once
        dlg.midi2wav(midifile, wavfile)
        dlg.show()


class AudioExportDialog(externalcommand.ExternalCommandDialog):

    """Dialog to show timidity output."""

    def __init__(self, parent, caption):
        super(AudioExportDialog, self).__init__(parent)
        self.setWindowModality(Qt.NonModal)
        self.setWindowTitle(caption)
        qutil.saveDialogSize(self, "audio_export/dialog/size", QSize(640, 400))

    def midi2wav(self, midfile, wavfile):
        """Run timidity to convert the MIDI to WAV."""
        self.wavfile = wavfile # we could need to clean it up...
        j = job.Job()
        j.decode_errors = 'replace'
        j.decoder_stdout = j.decoder_stderr = codecs.getdecoder('utf-8')
        j.command = ["timidity", midfile, "-Ow", "-o", wavfile]
        self.run_job(j)

    def cleanup(self, state):
        if state == "aborted":
            try:
                os.remove(self.wavfile)
            except OSError:
                pass


class Actions(actioncollection.ActionCollection):
    name = "file_export"
    def createActions(self, parent):
        self.export_musicxml = QAction(parent)
        self.export_audio = QAction(parent)

        self.export_musicxml.setIcon(icons.get("document-export"))
        self.export_audio.setIcon(icons.get("document-export"))

    def translateUI(self):
        self.export_musicxml.setText(_("Export Music&XML..."))
        self.export_musicxml.setToolTip(_("Export current document as MusicXML."))

        self.export_audio.setText(_("Export Audio..."))
        self.export_audio.setToolTip(_("Export to different audio formats."))

