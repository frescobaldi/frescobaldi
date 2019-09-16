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
The Job class and its descendants manage external processes
and capture the output to get it later or to have a log follow it.
"""


import codecs
import os
import time

from PyQt5.QtCore import (
    QCoreApplication,
    QProcess,
    QProcessEnvironment
)

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

    Jobs that run LilyPond will use objects of job.lilypond.Job or derived
    special classes.

    """
    output = signals.Signal()
    done = signals.Signal()
    started = signals.Signal()
    title_changed = signals.Signal()  # title (string)

    def __init__(
        self,
        command=[],
        args=None,
        directory=None,
        environment={},
        title="",
        input=None,
        input_file=None,
        output=None,
        output_file=None,
        priority=1,
        runner=None,
        decode_errors='strict',
        encoding='latin1'
    ):
        self._command = command if type(command) == list else [command]
        self._input = (
            input if type(input) == list
            else [input] if input is not None
            else []
        )
        self._input_file = (
            input_file if input_file is not None
            else self._input[-1] if self._input
            else []
        )
        self._output = (
            output if type(output) == list
            else [output] if output is not None
            else []
        )
        self._output_file = (
            output_file if output_file is not None
            else self._output[-1] if self._output
            else []
        )
        self._runner = runner
        self._arguments = args if args else []
        self._directory = directory
        self._environment = {}
        self._success = None
        self._error = None
        self._title = ""
        self._priority = priority
        self._aborted = False
        self._process = None
        self._history = []
        self._starttime = 0.0
        self._elapsed = 0.0
        self._encoding = encoding
        self._decoder_stderr = codecs.getdecoder(encoding)
        self._decoder_stdout = codecs.getdecoder(encoding)
        self._decode_errors = decode_errors  # codecs error handling

    def add_argument(self, arg):
        """Append an additional command line argument if it is not
        present already.
        arg may either be a single string or a key-value tuple."""
        k, v = arg if type(arg) == tuple else (arg, None)
        if k not in self._arguments:
            self._arguments.append(k)
            if v:
                self._arguments.append(v)

    def arguments(self):
        """
        Command arguments/options list.
        Each entry may be a string or a key-value tuple/list.
        In the default implementation they will be inserted after the
        command name.
        """
        return self._arguments

    def _cmd_add_arguments(self):
        """
        Add the arguments to the command, if present.
        Serialize tuples/lists if necessary.
        """
        for arg in self.arguments():
            if type(arg) in [tuple, list]:
                self._command.extend(arg)
            else:
                self._command.append(arg)

    def _cmd_add_input(self):
        """
        Add the input file or the input argument pair
        to the command, if present.
        """
        self._command.extend(self._input)

    def _cmd_add_output(self):
        """
        Add the output file or the output argument pair
        to the command, if present.
        """
        self._command.extend(self._output)

    def command(self):
        """
        Return the command (as string list).
        NOTE: Before configure_command() has been called
        this may not return useful values.
        """
        return self._command

    def directory(self):
        return self._directory

    def set_directory(self, directory):
        self._directory = directory

    def encoding(self):
        return self._encoding

    def environment(self, key=None):
        """
        Return either one environment variable
        or the whole dictionary (if key=None).
        """
        if key:
            return self._environment[key]
        else:
            return self._environment

    def set_environment(self, key, value):
        """
        Set a value in a job's environment.
        If value is None the environment variable is removed.
        """
        self._environment[key] = value

    def error(self):
        return self._error

    # TODO: Maybe the following four properties are not needed at all
    def input(self):
        return self._input

    def input_file(self):
        return self._input_file

    def output_arg(self):
        return self._output

    def output_file(self):
        return self._output_file

    def runner(self):
        """Return the Runner object if the job is run within
        a JobQueue, or None if not."""
        return self._runner

    def set_runner(self, runner):
        """Store a reference to a Runner if the job is run within
        a JobQueue."""
        self._runner = runner

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

    def priority(self):
        return self._priority

    def set_priority(self, value):
        self._priority = value

    def start(self):
        """Starts the process."""
        self.configure_command()
        self._command
        self._success = None
        self._error = None
        self._aborted = False
        self._history = []
        self._elapsed = 0.0
        self._starttime = time.time()
        if self._process is None:
            self.set_process(QProcess())
        self._process.started.connect(self.started)
        self.start_message()
        if os.path.isdir(self.directory() or ''):
            self._process.setWorkingDirectory(self.directory())
        if self.environment():
            self._update_process_environment()
        self._process.start(self._command[0], self._command[1:])

    def configure_command(self):
        """Process the command if necessary.

        Initially the command is the list given upon instantiation.
        The default implementation is to add (if present)
        - arguments
        - input file
        - output file
        to the initial command.

        To specify the command to be used it is possible to
        - instantiate job.Job and configure arguments, input and output
        - subclass job.Job and override the three composing functions
        - subclass job.Job and override configure_command.
        """
        # TODO: Maybe this order has to be made configurable
        # by storing the functions in a list and calling them
        # in a for loop - instead of requiring an override.
        self._cmd_add_arguments()
        self._cmd_add_input()
        self._cmd_add_output()

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
        return self._error == QProcess.FailedToStart

    def set_process(self, process):
        """Sets a QProcess instance and connects the signals."""
        self._process = process
        if process.parent() is None:
            process.setParent(QCoreApplication.instance())
        process.finished.connect(self._finished)
        process.error.connect(self._slot_error)
        process.readyReadStandardError.connect(self._readstderr)
        process.readyReadStandardOutput.connect(self._readstdout)

    def _update_process_environment(self):
        """(internal) initializes the environment for the process."""
        se = QProcessEnvironment.systemEnvironment()
        for k, v in self.environment().items():
            se.remove(k) if v is None else se.insert(k, v)
        self._process.setProcessEnvironment(se)

    def message(self, text, type=NEUTRAL):
        """
        Output some text as the given type
        (NEUTRAL, SUCCESS, FAILURE, STDOUT or STDERR).
        """
        self.output(text, type)
        self._history.append((text, type))

    def history(self, types=ALL):
        """
        Yield the output messages as two-tuples (text, type)
        since the process started.

        If types is given, it should be an OR-ed combination of the
        status types STDERR, STDOUT, NEUTRAL, SUCCESS or FAILURE.

        """
        for msg, type in self._history:
            if type & types:
                yield msg, type

    def stdout(self):
        """Return the standard output of the process as unicode text."""
        return "".join([line[0] for line in self.history(STDOUT)])

    def stderr(self):
        """Return the standard error of the process as unicode text."""
        return "".join([line[0] for line in self.history(STDERR)])

    def success(self):
        return self._success

    def _finished(self, exitCode, exitStatus):
        """(internal) Called when the process has finished."""
        self.finish_message(exitCode, exitStatus)
        success = exitCode == 0 and exitStatus == QProcess.NormalExit
        self._bye(success)

    def _slot_error(self, error):
        """(internal) Called when an error occurs."""
        self.error_message(error)
        if self._process.state() == QProcess.NotRunning:
            self._bye(False)

    def _bye(self, success):
        """(internal) Ends and emits the done() signal."""
        self._elapsed = time.time() - self._starttime
        if not success:
            self._error = self._process.error()
        self._success = success
        self._process.deleteLater()
        self._process = None
        self.done(success)

    def _readstderr(self):
        """(internal) Called when STDERR can be read."""
        output = self._process.readAllStandardError()
        self.message(
            self._decoder_stderr(output, self._decode_errors)[0], STDERR
        )

    def _readstdout(self):
        """(internal) Called when STDOUT can be read."""
        output = self._process.readAllStandardOutput()
        self.message(
            self._decoder_stdout(output, self._decode_errors)[0], STDOUT
        )

    def start_message(self):
        """Called by start().

        Outputs a message that the process has started.

        """
        name = self.title() or os.path.basename(self._command[0])
        self.message(_("Starting {job}...").format(job=name), NEUTRAL)

    def abort_message(self):
        """Called by abort().

        Outputs a message that the process has been aborted.

        """
        name = self.title() or os.path.basename(self._command[0])
        self.message(_("Aborting {job}...").format(job=name), NEUTRAL)

    def error_message(self, error):
        """Called when there is an error (by _slot_error()).

        Outputs a message describing the given QProcess.Error.

        """
        if error == QProcess.FailedToStart:
            self.message(_(
                "Could not start {program}.\n"
                "Please check path and permissions.").format(
                    program=self._command[0]
                ),
                FAILURE
            )
        elif error == QProcess.ReadError:
            self.message(_("Could not read from the process."), FAILURE)
        elif self._process.state() == QProcess.NotRunning:
            self.message(_("An unknown error occurred."), FAILURE)

    def finish_message(self, exitCode, exitStatus):
        """Called when the process finishes (by _finished()).

        Outputs a message on completion of the process.

        """
        if exitCode:
            self.message(_(
                "Exited with return code {code}."
            ).format(code=exitCode), FAILURE)
        elif exitStatus:
            self.message(_(
                "Exited with exit status {status}."
            ).format(status=exitStatus), FAILURE)
        else:
            time = self.elapsed2str(self.elapsed_time())
            self.message(_(
                "Completed successfully in {time}."
            ).format(time=time), SUCCESS)

    @staticmethod
    def elapsed2str(seconds):
        """Return a short display for the given time period (in seconds)."""
        minutes, seconds = divmod(seconds, 60)
        if minutes:
            return "{0:.0f}'{1:.0f}\"".format(minutes, seconds)
        return '{0:.1f}"'.format(seconds)
