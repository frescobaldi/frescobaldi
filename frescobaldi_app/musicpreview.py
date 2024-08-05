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

from PyQt6.QtCore import (
    QSize,
    Qt
)
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLabel, QStackedLayout, QVBoxLayout, QWidget)

import app
import icons
import job.lilypond
import log
import qutil
import pagedview
import widgets.progressbar


class MusicPreviewWidget(QWidget):
    def __init__(
        self,
        parent=None,
        showProgress=True,
        showWaiting=False,
        progressHidden=False,
        progressHiddenWhileIdle=True,
        progressShowFinished=3000,
        showLog=True
    ):
        super().__init__(parent)
        self._lastbuildtime = 10.0
        self._running = None
        self._current = None

        self._showLog = showLog
        if showLog:
            self._log = log.Log()
        self._showProgress = showProgress

        self._chooserLabel = QLabel()
        self._chooser = QComboBox(self, activated=self.selectDocument)
        self._view = pagedview.PagedView()
        self._view.setMagnifier(pagedview.Magnifier())

        self._showWaiting = showWaiting
        if showWaiting:
            from widgets.waitingoverlay import Overlay
            self._waiting = Overlay(self._view)
            self._waiting.hide()

        self._stack = QStackedLayout()
        self._top = QWidget()

        layout = QVBoxLayout(margin=0)
        self.setLayout(layout)

        layout.addWidget(self._top)
        layout.addLayout(self._stack)
        if self._showProgress:
            self._progress = widgets.progressbar.TimedProgressBar(
                parent=self,
                hidden=progressHidden,
                hideWhileIdle=progressHiddenWhileIdle,
                showFinished=progressShowFinished
            )
            layout.addWidget(self._progress)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(2)
        self._top.setLayout(top)
        top.addWidget(self._chooserLabel)
        top.addWidget(self._chooser)
        top.addStretch(1)

        if showLog:
            self._stack.addWidget(self._log)
        self._stack.addWidget(self._view)

        self._top.hide()
        app.aboutToQuit.connect(self.cleanup)
        app.translateUI(self)

    def translateUI(self):
        self._chooserLabel.setText(_("Document:"))

    def abort_running(self):
        """Ensures no running job is left behind.
        This *can* be called by the using dialog/widget."""
        j = self._running
        if j and j.is_running():
            if self._showLog:
                self._log.disconnectJob(j)
            j.done.disconnect(self._done)
            j.abort()

    def preview(
        self, text, title=None, base_dir=None,
        temp_dir='', cached=False
    ):
        """Runs LilyPond on the given text and shows the resulting PDF."""
        self.abort_running()
        if cached:
            self._running = j = job.lilypond.CachedPreviewJob(
                text,
                target_dir=temp_dir,
                base_dir=base_dir,
                title=title
            )
            if not self._running.needs_compilation():
                self._done(None)
                return
        else:
            self._running = j = job.lilypond.VolatileTextJob(
                text,
                title=title
            )
        j.done.connect(self._done)
        if self._showLog:
            self._log.clear()
            self._log.connectJob(j)
            self._stack.setCurrentWidget(self._log)
        if self._showProgress:
            j.started.connect(
                lambda: self._progress.start(self._lastbuildtime)
            )
            self._progress.start(self._lastbuildtime)
        if self._showWaiting:
            self._waiting.start()
        app.job_queue().add_job(j, 'generic')

    def _done(self, success):
        # TODO: Handle failed compilation (= no file to show)
        if self._showProgress:
            self._progress.stop()
        if self._showWaiting:
            self._waiting.stop()
        pdfs = self._running.resultfiles()
        self.setDocuments(pdfs)
        if not pdfs and self._showLog:
            self._stack.setCurrentWidget(self._log)
            return
        self._lastbuildtime = self._running.elapsed_time()
        self._stack.setCurrentWidget(self._view)
        if self._current:
            self._current.cleanup()
        self._current = self._running  # keep the tempdir
        self._running = None

    def setDocuments(self, pdfs):
        """Loads the given PDF path names in the UI."""
        self._documents = [pagedview.loadPdf(name) for name in pdfs]
        self._chooser.clear()
        self._chooser.addItems([os.path.basename(d.filename()) for d in self._documents])
        self._top.setVisible(len(self._documents) > 1)
        if pdfs:
            self._chooser.setCurrentIndex(0)
            self.selectDocument(0)
        else:
            self._view.clear()

    def selectDocument(self, index):
        self._view.setDocument(self._documents[index])

    def cleanup(self):
        if self._running:
            self._running.abort()
            self._running.cleanup()
            self._running = None
        if self._current:
            self._current.cleanup()
            self._current = None
        if self._showLog:
            self._stack.setCurrentWidget(self._log)
        self._top.hide()
        self._view.clear()

    def print_(self):
        """Prints the currently displayed document."""
        if self._view.document():
            self._view.print()


class MusicPreviewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self._widget = MusicPreviewWidget()
        layout.addWidget(self._widget)
        layout.addWidget(widgets.Separator())
        b = QDialogButtonBox()
        layout.addWidget(b)
        b.addButton(QDialogButtonBox.StandardButton.Close)
        b.rejected.connect(self.accept)
        self._printButton = b.addButton('', QDialogButtonBox.ButtonRole.ActionRole)
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
