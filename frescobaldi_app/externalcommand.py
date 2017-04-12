# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2015 - 2015 by Wilbert Berendsen and Pavel Roskin
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
Utilities to run external commands.
"""


import log
import widgets.dialog


class ExternalCommandDialog(widgets.dialog.Dialog):

    """Dialog that can run an external command, displaying the output.

    If the dialog is dismissed, the command is stopped and the cleanup()
    method is called.

    You need to create a Job instance with the command, and call the run_job()
    method to start it. The output is displayed in the dialog.

    When the user cancels the dialog while the command is running, cleanup() is
    called with the 'aborted' argument. When the user closes the dialog after
    the command has run, cleanup() is called with either the 'success' or
    'failure' argument, indicating whether the command exited normally.

    You can reimplement that method to do things like removing temporary files,
    etc.

    """
    def __init__(self, parent=None):
        super(ExternalCommandDialog, self).__init__(parent)
        self.log = log.Log(self)
        self.setMainWidget(self.log)
        self.finished.connect(self._closed)

    def run_job(self, job):
        """Run a job.Job()."""
        self.setMessage(_("Please wait until the command finishes"))
        self.setStandardButtons(('cancel',))
        self.job = job
        self.log.connectJob(job)
        job.done.connect(self._done)
        job.start()

    def _done(self):
        """(internal) Called when the job has finished."""
        self.setMessage(_("Command completed"))
        self.setStandardButtons(('ok',))

    def _closed(self):
        """(internal) Called when the user closes the dialog, calls cleanup()."""
        if self.job.success is None:
            self.job.abort()
            state = "aborted"
        elif self.job.success:
            state = "success"
        else:
            state = "failure"
        self.cleanup(state)

    def cleanup(self, state):
        """Called when the dialog is closed.

        state is one of three values:
        - "success": the command exited normally
        - "failure": the command exited with an error
        - "aborted": the dialog was cancelled while the command was running.

        Reimplement this method to do anything meaningful.

        """
        pass


