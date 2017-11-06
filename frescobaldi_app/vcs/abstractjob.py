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
Generic interface for synchronously and asynchronously running shell commands.
"""

import re
import time
import collections

from PyQt5.QtCore import QObject, QProcess, pyqtSignal


class Job(QObject):
    """Executes a single VCS command, either blocking or non-blocking.

    The output of the command will be stored in the _stdout and _stderr fields,
    run_blocking() will return the data while run() will invoke the finished
    signal, giving the caller the opportunity to retrieve the data.
    """

    # "custom" signals for passing on QProcess's signals
    finished = pyqtSignal(QObject, int)
    readyReadStandardError = pyqtSignal()
    readyReadStandardOutput = pyqtSignal()
    started = pyqtSignal()
    stateChanged = pyqtSignal(QProcess.ProcessState)
    errorOccurred = pyqtSignal(QProcess.ProcessError)

    # should be emitted in the body of signal finished's slot.
    executed = pyqtSignal(int)

    job_name = ''
    
    error_messages = {
        QProcess.FailedToStart : '{} failed to start',
        QProcess.Crashed : (_('{} crashed')),
        QProcess.Timedout : (_('{} timed out')),
        QProcess.ReadError : (_('{} ReadError')),
        QProcess.WriteError : (_('{} WriteError')),
        QProcess.UnknownError : (_('Unknown {} Error'))
    }

    def __init__(self, root_path=None):
        super(Job, self).__init__()
        # args could be set in advance
        self.preset_args = None

        self._version = None
        self._stderr = None
        self._stdout = None

        # Create and configure QProcess object
        self._process = process = QProcess()
        process.setProgram(self.executable)
        if root_path is not None:
            process.setWorkingDirectory(root_path)

        # Connect QProcess's signals to our own intermediate slots or our own signals
        process.finished.connect(self._finished)
        process.readyReadStandardError.connect(self.readyReadStandardError)
        process.readyReadStandardOutput.connect(self.readyReadStandardOutput)
        process.started.connect(self.started)
        process.stateChanged.connect(self.stateChanged)

        # Note:
        # Signal "errorOccurred" is listed as an attribute in QProcess in PyQt5
        # And it is available in PyQt-5.8.2. Reference: https://stackoverflow.com/questions/44868741/is-qqueue-missing-from-pyqt-5
        # It is still not available in our current development environment PyQt-5.5.1
        # So we use its obsolete version "error"
        try:
            process.errorOccurred.connect(self.errorOccurred)
        except AttributeError:
            process.error.connect(self.errorOccurred)

    @classmethod
    def version(cls):
        """
        Return the version of the invoked shell command
        as a tuple or False if it is not installed
        """
        raise NotImplementedError()
    
    @classmethod
    def error(cls, reason):
        """
        Format a process's error message using the job name.
        """
        return cls.error_messages[reason].format(cls.job_name)

    def _start_process(self, args):
        """
        Internal command preparing and starting the process
        """
        if args is None:
            raise Exception(_(
                "Trying to start '{}' job without arguments".format(self.job_name)))
        self._stderr = None
        self._stdout = None
        self._process.setArguments(args)
        self._process.start()

    def run(self, args = None):
        """
        Asynchronously run the command.

        Arguments:
                  args([]): arguments of the shell command.
                            If 'args' is not given, 'preset_args' will be used.
                            The first argument is the command to be invoked.

        Results will only be available after the _finished() slot has been executed
        """
        args = self.preset_args if args is None else args
        self._start_process(args)

    def run_blocking(self, args = None, isbinary = False):
        """
        Synchronously run the command.

        Arguments:
                  args([]): arguments of the shell command.
                            If 'args' is not given, 'preset_args' will be used.
                            The first argument is the command to be invoked.
            isbinary(bool): True - return the binary result.
                            False - return the 'utf-8' encoded string list.

        Results will be returned but are also available through stdout() and stderr() afterwards
        """
        args = self.preset_args if args is None else args
        self._start_process(args)
        self._process.waitForFinished()
        return (self.stdout(isbinary), self.stderr(isbinary))

    def isRunning(self):
        """
        Returns True if the process is currently running.
        """
        return not self._process.state() == QProcess.NotRunning

    def kill(self):
        """
        Kills the process if it is running
        """
        if self.isRunning():
            # Note: Qt handles the OS differences transparently
            self._process.kill()

    def _handle_results(self):
        """
        will be called when the process has completed.
        Populates the result fields
        """
        self._stderr = self._process.readAllStandardError()
        self._stdout = self._process.readAllStandardOutput()

    def _finished(self, exitcode, exitstatus):
        """
        Called when the process has completed.
        process results and forward the signal

        exitcode == 0 : Process executes successfully.
                        Result will output to stdout().
        exitcode == 1 : Process returns an error message.
                        Error message will output to stderr()
        """
        self._handle_results()
        self.finished.emit(self, exitcode)

    def stdout(self, isbinary = False):
        """
        Returns the content of the stdout output, if any.

        Returns:
            None: Job() is running / Job() hasn't started / Job() has crashed
             b'': isbinary is True.
                  Job() has finished running and returns a binary result.
              []: isbinary is False.
                  Job() has finished running and returns a string-list result.
        """
        if self._stdout is None:
            return None

        if isbinary:
            return self._stdout
        else:
            return self._binary_to_string_list(self._stdout)

    def stderr(self, isbinary = False):
        """
        Returns the content of the stderr output, if any.

        Returns:
            None: Job() is running / Job() hasn't started / Job() has crashed
             b'': isbinary is True.
                  Job() has finished running and returns a binary result.
              []: isbinary is False.
                  Job() has finished running and returns a string-list result.
        """
        if self._stderr is None:
            return None

        if isbinary:
            return self._stderr
        else:
            return self._binary_to_string_list(self._stderr)

    def _binary_to_string_list(self, binary_content):
        """
        Encode the binary content into a 'utf-8' string list.
        """
        res = str(binary_content, 'utf-8').split('\n')
        if not res[-1]:
            res.pop()
        return res



class JobQueue(QObject):
    """JobQueue is the command queue managing Job() objects

    You may need this when you want to run some asynchronous commands in order.
    Job() objects in the queue run one after another.  When an error occurrs
    during runing, JobQueue will stop running and emits an "errorOccurred"
    signal.
    """

    errorOccurred = pyqtSignal(QProcess.ProcessError)

    def __init__(self):
        super(JobQueue, self).__init__()
        self._queue = []

    def enqueue(self, gitjob):
        """
        Appends a Job() object (gitjob) into the queue.
        If the queue is empty, the Job() object will run immediately.

        CAUTION:
        enqueue a same Job() object multiple times will lead to a runtime-error.
        """
        gitjob.executed.connect(self.run_next)
        gitjob.errorOccurred.connect(self.errorOccurred)

        self._queue.append(gitjob)
        if len(self._queue) == 1:
            # args of Git process has been set in advance
            self._queue[0].run()

    def kill_all(self):
        """
        Kills and removes all the Job() objects this queue contains
        """
        self._remove_current()
        for job in self._queue:
            job.deleteLater()
        self._queue.clear()

    def _optimize(self):
        cmd_set = set()
        for job in self._queue:
            args_str = "".join(job.preset_args)
            if args_str not in cmd_set:
                self._queue[len(cmd_set)] = job
                cmd_set.add(args_str)
        self._queue = self._queue[:len(cmd_set)]

    def run_next(self, execute_status = 0):
        """
        Runs next Job() object in the queue.
        It can be triggered by the previous Job() instance's executed signal.
        """
        self._remove_current()
        self._optimize()
        if self._queue:
            self._queue[0].run()

    def _remove_current(self):
        """
        Removes the Job() object in queue-head.
        If the Job() object is running, terminate it by calling its kill().
        """
        if self._queue:
            if self._queue[0].isRunning():
                # prevent the git errorOccurred signals being handled
                self._queue[0].errorOccurred.disconnect()
                self._queue[0].kill()
            self._queue[0].deleteLater()
            del self._queue[0]

