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
A Job runs LilyPond (or another process) and captures the output
to get it later or to have a log follow it.
"""


import codecs
import os
import time

from PyQt5.QtCore import QCoreApplication, QProcess, QProcessEnvironment

import signals


# message status:
STDOUT  = 1
STDERR  = 2
NEUTRAL = 4
SUCCESS = 8
FAILURE = 16

# output from the process
OUTPUT = STDERR | STDOUT

# status messages
STATUS = NEUTRAL | SUCCESS | FAILURE

# all
ALL = OUTPUT | STATUS


class Job(object):
    """Manages a process.

    Set the command attribute to a list of strings describing the program and
    its arguments.
    Set the directory attribute to a working directory.
    The environment attribute is a dictionary; if you set an item it will be
    added to the environment for the process (the rest will be inherited from
    the system); if you set an item to None, it will be unset.

    Call start() to start the process.
    The output() signal emits output (stderr or stdout) from the process.
    The done() signal is always emitted when the process has ended.
    The history() method returns all status messages and output so far.

    When the process has finished, the error and success attributes are set.
    The success attribute is set to True When the process exited normally and
    successful. When the process did not exit normally and successfully, the
    error attribute is set to the QProcess.ProcessError value that occurred
    last. Before start(), error and success both are None.

    The status messages and output all are in one of five categories:
    STDERR, STDOUT (output from the process) or NEUTRAL, FAILURE or SUCCESS
    (status messages). When displaying these messages in a log, it is advised
    to take special care for newlines, esp when a status message is displayed.
    Status messages normally have no newlines, so you must add them if needed,
    while output coming from the process may continue in the same line.

    """
    output = signals.Signal()
    done = signals.Signal()
    title_changed = signals.Signal() # title (string)

    def __init__(self):
        self.command = []
        self.directory = ""
        self.environment = {}
        self.success = None
        self.error = None
        self._title = ""
        self._aborted = False
        self._process = None
        self._history = []
        self._starttime = 0.0
        self._elapsed = 0.0
        self.decoder_stdout = self.create_decoder(STDOUT)
        self.decoder_stderr = self.create_decoder(STDERR)
        self.decode_errors = 'strict'  # codecs error handling

    def create_decoder(self, channel):
        """Return a decoder for the given channel (STDOUT/STDERR).

        This method is called from the constructor. You can re-implement this
        method to return another decoder, or you can set the decoders manually
        by setting the `decoder_stdout` and `decoder_stderr` manually after
        construction.

        This decoder is then used to decode the 8bit bytestrings into Python
        unicode strings. The default implementation returns a 'latin1'
        decoder for both channels.

        """
        return codecs.getdecoder('latin1')

    def title(self):
        """Return the job title, as set with set_title().

        The title defaults to an empty string.

        """
        return self._title

    def set_title(self, title):
        """Set the title.

        If the title changed, the title_changed(title) signal is emitted.

        """
        old, self._title = self._title, title
        if title != old:
            self.title_changed(title)

    def start(self):
        """Starts the process."""
        self.success = None
        self.error = None
        self._aborted = False
        self._history = []
        self._elapsed = 0.0
        self._starttime = time.time()
        if self._process is None:
            self.set_process(QProcess())
        self.start_message()
        if os.path.isdir(self.directory):
            self._process.setWorkingDirectory(self.directory)
        if self.environment:
            self._update_process_environment()
        self._process.start(self.command[0], self.command[1:])

    def start_time(self):
        """Return the time this job was started.

        Returns 0.0 when the job has not been started yet.

        """
        return self._starttime

    def elapsed_time(self):
        """Return how many seconds this process has been running."""
        if self._elapsed:
            return self._elapsed
        elif self._starttime:
            return time.time() - self._starttime
        return 0.0

    def abort(self):
        """Abort the process."""
        if self._process:
            self._aborted = True
            self.abort_message()
            if os.name == "nt":
                self._process.kill()
            else:
                self._process.terminate()

    def is_aborted(self):
        """Returns True if the job was aborted by calling abort()."""
        return self._aborted

    def is_running(self):
        """Returns True if this job is running."""
        return bool(self._process)

    def failed_to_start(self):
        """Return True if the process failed to start.

        (Call this method after the process has finished.)

        """
        return self.error == QProcess.FailedToStart

    def set_process(self, process):
        """Sets a QProcess instance and connects the signals."""
        self._process = process
        if process.parent() is None:
            process.setParent(QCoreApplication.instance())
        process.finished.connect(self._finished)
        process.error.connect(self._error)
        process.readyReadStandardError.connect(self._readstderr)
        process.readyReadStandardOutput.connect(self._readstdout)

    def _update_process_environment(self):
        """(internal) initializes the environment for the process."""
        se = QProcessEnvironment.systemEnvironment()
        for k, v in self.environment.items():
            se.remove(k) if v is None else se.insert(k, v)
        self._process.setProcessEnvironment(se)

    def message(self, text, type=NEUTRAL):
        """Output some text as the given type (NEUTRAL, SUCCESS, FAILURE, STDOUT or STDERR)."""
        self.output(text, type)
        self._history.append((text, type))

    def history(self, types=ALL):
        """Yield the output messages as two-tuples (text, type) since the process started.

        If types is given, it should be an OR-ed combination of the status types
        STDERR, STDOUT, NEUTRAL, SUCCESS or FAILURE.

        """
        for msg, type in self._history:
            if type & types:
                yield msg, type

    def stdout(self):
        """Return the standard output of the process as unicode text."""
        return "".join(self.history(STDOUT))

    def stderr(self):
        """Return the standard error of the process as unicode text."""
        return "".join(self.history(STDERR))

    def _finished(self, exitCode, exitStatus):
        """(internal) Called when the process has finished."""
        self.finish_message(exitCode, exitStatus)
        success = exitCode == 0 and exitStatus == QProcess.NormalExit
        self._bye(success)

    def _error(self, error):
        """(internal) Called when an error occurs."""
        self.error_message(error)
        if self._process.state() == QProcess.NotRunning:
            self._bye(False)

    def _bye(self, success):
        """(internal) Ends and emits the done() signal."""
        self._elapsed = time.time() - self._starttime
        if not success:
            self.error = self._process.error()
        self.success = success
        self._process.deleteLater()
        self._process = None
        self.done(success)

    def _readstderr(self):
        """(internal) Called when STDERR can be read."""
        output = self._process.readAllStandardError()
        self.message(self.decoder_stderr(output, self.decode_errors)[0], STDERR)

    def _readstdout(self):
        """(internal) Called when STDOUT can be read."""
        output = self._process.readAllStandardOutput()
        self.message(self.decoder_stdout(output, self.decode_errors)[0], STDOUT)

    def start_message(self):
        """Called by start().

        Outputs a message that the process has started.

        """
        name = self.title() or os.path.basename(self.command[0])
        self.message(_("Starting {job}...").format(job=name), NEUTRAL)

    def abort_message(self):
        """Called by abort().

        Outputs a message that the process has been aborted.

        """
        name = self.title() or os.path.basename(self.command[0])
        self.message(_("Aborting {job}...").format(job=name), NEUTRAL)

    def error_message(self, error):
        """Called when there is an error (by _error()).

        Outputs a message describing the given QProcess.Error.

        """
        if error == QProcess.FailedToStart:
            self.message(_(
                "Could not start {program}.\n"
                "Please check path and permissions.").format(program = self.command[0]), FAILURE)
        elif error == QProcess.ReadError:
            self.message(_("Could not read from the process."), FAILURE)
        elif self._process.state() == QProcess.NotRunning:
            self.message(_("An unknown error occurred."), FAILURE)

    def finish_message(self, exitCode, exitStatus):
        """Called when the process finishes (by _finished()).

        Outputs a message on completion of the process.

        """
        if exitCode:
            self.message(_("Exited with return code {code}.").format(code=exitCode), FAILURE)
        elif exitStatus:
            self.message(_("Exited with exit status {status}.").format(status=exitStatus), FAILURE)
        else:
            time = self.elapsed2str(self.elapsed_time())
            self.message(_("Completed successfully in {time}.").format(time=time), SUCCESS)

    @staticmethod
    def elapsed2str(seconds):
        """Return a short display for the given time period (in seconds)."""
        minutes, seconds = divmod(seconds, 60)
        if minutes:
            return "{0:.0f}'{1:.0f}\"".format(minutes, seconds)
        return '{0:.1f}"'.format(seconds)


