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
A widget and dialog to show an output preview of a LilyPond document.
"""



import os
import glob
import shutil

from PyQt5.QtCore import QSettings, QSize
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLabel, QStackedLayout, QVBoxLayout, QWidget)

import ly.document
import ly.docinfo

import app
import codecs
import icons
import job
import log
import util
import qutil
import lilypondinfo
import popplerview
import popplertools
import widgets.progressbar


class MusicPreviewJob(job.Job):
    def __init__(self, text, title=None):
        super(MusicPreviewJob, self).__init__()
        self.decode_errors = 'replace'
        self.decoder_stdout = self.decoder_stderr = codecs.getdecoder('utf-8')
        self.directory = util.tempdir()
        self.document = os.path.join(self.directory, 'document.ly')
        with open(self.document, 'wb') as f:
            f.write(text.encode('utf-8'))

        info = lilypondinfo.preferred()
        if QSettings().value("lilypond_settings/autoversion", True, bool):
            version = ly.docinfo.DocInfo(ly.document.Document(text, 'lilypond')).version()
            if version:
                info = lilypondinfo.suitable(version)

        lilypond = info.abscommand() or info.command
        self.command = [lilypond, '-dno-point-and-click', '--pdf', self.document]
        if title:
            self.set_title(title)

    def resultfiles(self):
        return glob.glob(os.path.join(self.directory, '*.pdf'))

    def cleanup(self):
        shutil.rmtree(self.directory, ignore_errors=True)


class MusicPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super(MusicPreviewWidget, self).__init__(parent)
        self._lastbuildtime = 10.0
        self._running = None
        self._current = None

        self._chooserLabel = QLabel()
        self._chooser = QComboBox(self, activated=self.selectDocument)
        self._log = log.Log()
        self._view = popplerview.View()
        self._progress = widgets.progressbar.TimedProgressBar()

        self._stack = QStackedLayout()
        self._top = QWidget()

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self._top)
        layout.addLayout(self._stack)
        layout.addWidget(self._progress)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(2)
        self._top.setLayout(top)
        top.addWidget(self._chooserLabel)
        top.addWidget(self._chooser)
        top.addStretch(1)

        self._stack.addWidget(self._log)
        self._stack.addWidget(self._view)

        self._top.hide()
        app.aboutToQuit.connect(self.cleanup)
        app.translateUI(self)

    def translateUI(self):
        self._chooserLabel.setText(_("Document:"))

    def preview(self, text, title=None):
        """Runs LilyPond on the given text and shows the resulting PDF."""
        j = self._running = MusicPreviewJob(text, title)
        j.done.connect(self._done)
        self._log.clear()
        self._log.connectJob(j)
        j.start()
        self._progress.start(self._lastbuildtime)

    def _done(self, success):
        self._progress.stop(False)
        pdfs = self._running.resultfiles()
        self.setDocuments(pdfs)
        if not pdfs:
            self._stack.setCurrentWidget(self._log)
            return
        self._lastbuildtime = self._running.elapsed_time()
        self._stack.setCurrentWidget(self._view)
        if self._current:
            self._current.cleanup()
        self._current = self._running # keep the tempdir
        self._running = None

    def setDocuments(self, pdfs):
        """Loads the given PDF path names in the UI."""
        self._documents = [popplertools.Document(name) for name in pdfs]
        self._chooser.clear()
        self._chooser.addItems([d.name() for d in self._documents])
        self._top.setVisible(len(self._documents) > 1)
        if pdfs:
            self._chooser.setCurrentIndex(0)
            self.selectDocument(0)
        else:
            self._view.clear()

    def selectDocument(self, index):
        doc = self._documents[index].document()
        if doc:
            self._view.load(doc)

    def cleanup(self):
        if self._running:
            self._running.abort()
            self._running.cleanup()
            self._running = None
        if self._current:
            self._current.cleanup()
            self._current = None
        self._stack.setCurrentWidget(self._log)
        self._top.hide()
        self._view.clear()

    def print_(self):
        """Prints the currently displayed document."""
        if self._documents:
            doc = self._documents[self._chooser.currentIndex()]
            import popplerprint
            popplerprint.printDocument(doc, self)


class MusicPreviewDialog(QDialog):
    def __init__(self, parent=None):
        super(MusicPreviewDialog, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self._widget = MusicPreviewWidget()
        layout.addWidget(self._widget)
        layout.addWidget(widgets.Separator())
        b = QDialogButtonBox()
        layout.addWidget(b)
        b.addButton(QDialogButtonBox.Close)
        b.rejected.connect(self.accept)
        self._printButton = b.addButton('', QDialogButtonBox.ActionRole)
        self._printButton.setIcon(icons.get("document-print"))
        self._printButton.clicked.connect(self._widget.print_)
        self._printButton.hide()
        qutil.saveDialogSize(self, "musicpreview/dialog/size", QSize(500, 350))
        app.translateUI(self)

    def translateUI(self):
        self._printButton.setText(_("&Print"))
        self.setWindowTitle(app.caption(_("Music Preview")))

    def preview(self, text, title=None):
        self._widget.preview(text, title)

    def cleanup(self):
        self._widget.cleanup()

    def setEnablePrintButton(self, enable):
        """Enables or disables the print button."""
        self._printButton.setVisible(enable)


