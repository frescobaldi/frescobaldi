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
Execute a single Git command, either blocking or non-blocking.
The output of the command will be stored in the _stdout and _stderr fields,
run_blocking() will return the data while run() will invoke the finished signal,
giving the caller the opportunity to retrieve the data.
"""

import os
import re
import time

from PyQt5.QtCore import QObject, QProcess, pyqtSignal


class GitError(Exception):
    pass

class Git(QObject):
    done = pyqtSignal(bool)

    # "custom" signals for passing on QProcess's signals
    errorOccured(QProcess.ProcessError)
    finished = pyqtSignal(int, QProcess.ExitStatus)
    readyReadStandardError = pyqtSignal()
    readyReadStandardOutput = pyqtSignal()
    started = pyqtSignal()
    stateChanged = pyqtSignal(QProcess.ProcessState)

    def __init__(self, owner):
        super(Git, self).__init__(owner)
        # TODO: check for preference
        self._executable = 'git'
        # TODO: change to a .root() method in gitrepo.Repo()
        self._workingdirectory = owner.root_path
        self._version = None
        self._isbinary = False
        self._stderr = None
        self._stdout = None

        # Create and configure QProcess object
        self._process = process = QProcess()
        process.setProgram(self._executable)
        process.setWorkingDirectory(self._workingdirectory)
        process.errorOccured.connect(self.slotErrorOccured)

        # Connect QProcess's signals to our own intermediate slots or our own signals
        process.finished.connect(self._finished)
        process.readyReadStandardError.connect(self.readyReadStandardError)
        process.readyReadStandardOutput.connect(self.readStandardOutput)
        process.started.connect(self.started)
        process.stateChanged.connect(self.stateChanged)

    def _start_process(self, args, isbinary=False):
        """
        Internal command preparing and starting the Git process
        """
        self._stderr = ''
        self._stdout = ''
        self._isbinary = isbinary
        self._process.setArguments(args)
        self._process.start()

    def run(self, args, isbinary=False):
        """
        Asynchronously run the command.
        Results will only be available after the _finished() slot has been executed
        """
        self._start_process(args, isbinary)

    def run_blocking(self, args, isbinary = False):
        """
        Synchronously run the command.
        Results will be returned but are also available through stdout() and stderr() afterwards
        """
        self._process.finished.disconnect()
        self._start_process(args, isbinary)
        self._process.waitForFinished()
        self._handle_results()
        self._process.finished.connect(self._finished)
        # ? TODO: I think we should return a (_stdout, _stderr) tuple
        return self._stdout

    def isRunning(self):
        """
        Returns True if the process is currently running.
        """
        return not self._process.state() == QProcess.NotRunning

    def kill(self):
        """
        Kills the process if it is running
        """
        if not self.isRunning():
            # Note: Qt handles the OS differences transparently
            self._process.kill()

    def _tic(self):
        """
        Helper function to count how much time a git command takes
        """
        self._timer = time.perf_counter()

    def _toc(self, args = []):
        """
        Helper function to count how much time a git command takes
        """
        if self._timer:
            print('command git {} takes {}'.format(' '.join(args), 
                time.perf_counter()-self._timer))
            self._timer = None

    def _handle_results(self):
        """
        will be called when the process has completed.
        Populates the result fields
        """
        if self._isbinary:
            self._stderr = self._process.readAllStandardError()
            self._stdout = self._process.readAllStandardOutput()
        else:
            self._stdout = str(self._process.readAllStandardError(), 'utf-8').split('\n')
            if not self._stdout[-1]:
                self._stdout.pop()
            self._stderr = str(self._process.readAllStandardError(), 'utf-8').split('\n')
            if not self._stderr[-1]:
                self._stderr.pop()

        # TODO: Discuss this. Actually we should change this and pass the responsibility to decide to the caller
        if self._stderr:
            raise GitError(stderr)

    def _finished(self):
        """
        Called when the process has completed.
        process results and forward the signal
        """
        self._handle_results()
        self.finished.emit()

    def stdout(self):
        """
        Returns the content of the stdout output, if any.
        """
        if self._stdout:
            return self._stdout
        else:
            # TODO: Discuss what should happen here
            return None

    def stderr(self):
        """
        Returns the content of the stderr output, if any.
        """
        if self._stderr:
            return self._stderr
        else:
            # TODO: Discuss what should happen here
            return None

    # TODO: is it a good place to keep this command
    # We can assume (can we?) the Git version not to change within a session,
    # so could there be a more global place where this information could be cached?
    def version(self):
        """
        Return git executable version.

        The version string is used to check, whether git executable exists and
        works properly. It may also be used to enable functions with newer git
        versions.

        Returns:
            tuple: PEP-440 conform git version (major, minor, patch)
        """
        if self._version:
            return self._version
        args = ['--version']
        # Query git version synchronously
        output = self.run_blocking(args) or ''
        # Parse version string like (git version 2.12.2.windows.1)
        match = re.match(r'git version (\d+)\.(\d+)\.(\d+)', output[0])
        if match:
            # PEP-440 conform git version (major, minor, patch)
            self._version = tuple(int(g) for g in match.groups())
            return self._version
        else:
            # TODO: Implement this case
            pass

    # Deprecated
    # I don't think we need that. directory is set in __init__
    def setWorkingDirectory(self, workingdirectory):
        self._process.setWorkingDirectory(workingdirectory)
        self._workingdirectory = workingdirectory

    # Deprecated
    # Probably we'll never need this
    def workingDirectory(self):
        return self._workingdirectory

    # Deprecated
    # I don't think we need that. executable is set in __init__
    def setGitExecutable(self, executable):
        self._process.setProgram(executable)
        self._executable = executable

    # Deprecated
    # Probably we'll never need this
    def gitExecutable(self):
        return self._executable

    # Deprecated
    def killCurrent(self):
        if self.isRunning():
            self._queue[0]['process'].finished.disconnect()
            # termination should be sync?
            if os.name == "nt":
                self._queue[0]['process'].kill()
            else:
                self._queue[0]['process'].terminate()
            del self._queue[0]

    # Deprecated.
    # We don't even have a queue anymore
    def killAll(self):
        self.killCurrent()
        self._queue = []
