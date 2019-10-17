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
        app.jobFinished.connect(self.set_export_audio)
        # TODO: Also connect to a signal that is emitted
        # whenever the current document has changed.

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
        orgname = doc.url().toLocalFile()
        midifile = resultfiles.results(doc).files('.mid*')[0]
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

    def set_export_audio(self, doc):
        """Enable/Disable the export_audio action.

        The action will be enabled if
        - at least one tool is avaibable AND
        - the current document has existing MIDI file(s)
        """
        midfiles = resultfiles.results(doc).files('.mid*')
        action = self.actionCollection.export_audio
        enabled = True if midfiles and audio_available(True) else False
        action.setEnabled(enabled)
        action.setToolTip(self.set_audio_tooltip(action, midfiles))

    def set_audio_tooltip(self, action, midfiles):
        """Generate the tooltip for the export_audio action.

        This has to be done "live" to reflect the availability
        of converters and the state of the current document.
        """
        result = []
        result.append(_("Export to different audio formats if a"))
        result.append(_("supported converter is available and the"))
        result.append(_("current document has produced MIDI file(s)."))
        result.append(_("Available exporters:"))
        available = audio_available()
        for supported in _supported_tools:
            result.append("- {tool}: {available}".format(
                tool=supported,
                available=_("Yes") if supported in available else _("No")
            ))
        result.append(_("Document has MIDI file(s): {midi}").format(
            midi=_("Yes") if midfiles else _("No")
        ))
        return '\n'.join(result)


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


_supported_tools = ['timidity']
_available_tools = None

def audio_available(force=False):
    """Return a list of supported audio export tools.

    This is cached by default but rechecking can be forced.
    For example when populating the export menu it is always reloaded
    because typically a user will install a tool if it missing and
    does *not* want to restart Frescobaldi afterwards.."""

    global _available_tools
    if force or _available_tools is None:
        from shutil import which
        _audio_available = []
        for tool in _supported_tools:
            if which(tool) is not None:
                _audio_available.append(tool)
    return _audio_available
