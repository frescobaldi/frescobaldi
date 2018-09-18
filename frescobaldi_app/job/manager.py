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
A JobManager exists for every Document, and ensures no two jobs are running
at the same time.

It also sends the app-wide signals jobStarted() and jobFinished().

"""


import app
import plugin
import signals


def manager(document):
    return JobManager.instance(document)


def job(document):
    return JobManager.instance(document).job()


def is_running(document):
    if job(document):
        return job(document).is_running()
    return False


class JobManager(plugin.DocumentPlugin):

    started = signals.Signal()  # Job
    finished = signals.Signal() # Job, success

    def __init__(self, document):
        self._job = None

    def start_job(self, job):
        """Starts a Job on our behalf."""
        if not self.is_running():
            self._job = job
            job.done.connect(self._finished)
            job.start()
            self.started(job)
            app.jobStarted(self.document(), job)

    def _finished(self, success):
        self.finished(job, success)
        app.jobFinished(self.document(), self._job, success)

    def job(self):
        """Returns the last job if any."""
        return self._job

    def is_running(self):
        """Returns True when a job is running."""
        if self._job:
            return self._job.is_running() and not self._job.is_aborted()



