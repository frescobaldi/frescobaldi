# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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
A Dialog to run an external command and simply show the log.
"""

from PyQt6.QtCore import Qt, QSize

import log
import qutil
import signals
import widgets.dialog

class Dialog(widgets.dialog.Dialog):
    """Dialog to run arbitrary external job.Job commands and show the log."""

    job_done = signals.Signal()

    def __init__(self, parent, auto_accept=False):
        super().__init__(
            parent,
            buttons=('cancel', 'ok',)
        )
        self.setWindowModality(Qt.WindowType.WindowModal)
        self.setIconSize(32)
        self.auto_accept = auto_accept
        self.log = log.Log(self)
        self.job = None
        self.setMainWidget(self.log)
        qutil.saveDialogSize(self, "job-dialog/dialog/size", QSize(480, 800))

    def abort_job(self):
        self.job.abort()
        self.reject()

    def run(self, j, msg=_("Run external command")):
        """Run the given job."""
        self.job = j
        self.job.done.connect(self.slot_job_done)
        self.log.connectJob(j)
        self.setWindowTitle(j.title())
        self.setMessage(msg)
        self.button('ok').setEnabled(False)
        self.button('cancel').clicked.connect(self.abort_job)
        j.start()
        self.exec()

    def slot_job_done(self):
        if self.job.success:
            if self.auto_accept:
                self.accept()
            self.button('ok').setEnabled(True)
        else:
            self.setMessage(_("Job failed! Please inspect log"))
            self.setIcon('critical')
        self.button('cancel').clicked.connect(self.reject)
        self.job_done.emit()
