# process.py -- A very simple wrapper around QProcess
#
# Copyright (c) 2012 by Wilbert Berendsen
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
A very simple wrapper around QProcess, and a scheduler to enable running
one process at a time.
"""

__all__ = ['Process', 'Scheduler']

from PyQt5.QtCore import QObject, QProcess, pyqtSignal


class Process(QObject):
    """A very simple wrapper to run a QProcess.

    Initialize the process with the command line (as a list) to run.
    Then (or later) call start() to run it. At that moment the 'process'
    attribute is available, which contains the QProcess instance managing
    the process.

    The done() signal is emitted with a boolean success value. In slots
    connected (synchronously) the process attribute is still available.

    """

    done = pyqtSignal(bool)

    def __init__(self, command):
        """Sets up the command to run."""
        QObject.__init__(self)
        self.command = command

    def start(self):
        """Really starts a QProcess, executing the command line."""
        self.setup()
        self.process.start(self.command[0], self.command[1:])

    def setup(self):
        """Called on start(), sets up the QProcess in the process attribute."""
        self.process = p = QProcess()
        p.finished.connect(self._finished)
        p.error.connect(self._error)

    def _finished(self, exitCode):
        self._done(exitCode == 0)

    def _error(self):
        self._done(False)

    def _done(self, success):
        self.done.emit(success)
        self.cleanup()

    def cleanup(self):
        """Deletes the process."""
        self.process.deleteLater()
        del self.process


class Scheduler(object):
    """A very simple scheduler that runs one Process at a time.

    You can use this to run e.g. commandline tools asynchronously and you
    don't want to have them running at the same time.

    """
    def __init__(self):
        self._schedule = []

    def add(self, process):
        """Adds the process to run."""
        process.done.connect(self._done)
        self._schedule.append(process)
        if len(self._schedule) == 1:
            self._schedule[0].start()

    def remove(self, process):
        """Removes the process from the schedule.

        This only works if the process has not been started yet.

        """
        if process in self._schedule[1:]:
            self._schedule.remove(process)
            process.done.disconnect(self._done)

    def _done(self):
        del self._schedule[0]
        if self._schedule:
            self._schedule[0].start()


