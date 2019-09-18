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
    QObject,
    QProcess,
    QProcessEnvironment,
)

import app
import signals

from . import queue


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


def elapsed2str(seconds):
    """Return a short display for the given time period (in seconds)."""
    minutes, seconds = divmod(seconds, 60)
    if minutes:
        return "{0:.0f}'{1:.0f}\"".format(minutes, seconds)
    return '{0:.1f}"'.format(seconds)


class Job(QObject):
    """Manages a process.

    Configure the process through the key=value arguments to __init__
    or later (but before starting the job) through property setters.

    Call start() to start the process.
    By default this will enqueue the job in a JobQueue held by the
    global job queue. Only if the queue has explicitly been set to None
    (by set_queue(None) or the `queue` init argument) the job is started
    immediately.
    The job queue will either enqueue the job (potentially respecting the
    `priority` property) or immediately start the job.
    When actually starting the job several things happen:
    - configure_command() will be called to compose the command to be used.
      By default this will list the command name, arguments, input and output
      (if present). Subclasses should override
      - the _cmd_add_XXX methods
        to configure how the slices are composed or
      - the configure_command method
        for more fundamental changes to the way a command is created.
    - The output() signal emits output (stderr or stdout) from the process.
    - The done() signal is always emitted when the process has ended.
    - The history() method returns all status messages and output so far.

    When the process has finished, the error() and success() properties are set.
    The success() property is set to True when the process exited normally and
    successful. When the process did not exit normally and successfully, the
    error() property is set to the QProcess.ProcessError value that occurred
    last. Before start(), error() and success() both are None.

    The status messages and output all are in one of five categories:
    STDERR, STDOUT (output from the process) or NEUTRAL, FAILURE or SUCCESS
    (status messages). When displaying these messages in a log, it is advised
    to take special care of newlines, esp. when a status message is displayed.
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
        parent=app.qApp,
        command=[],
        args=[],
        directory=None,
        environment={},
        title=None,
        show_command_info=None,
        input=None,
        input_file=None,
        output=None,
        output_file=None,
        decode_errors='strict',
        encoding='latin1',
        priority=1,
        queue='generic',
        no_queue=False
    ):
        """
        The following optional arguments can be pre-set (or specified later):
        - parent (A QObject)
        - command
          a string list with the command name as its first element,
          optionally followed by arguments
        - args
          arguments (as string list), if not already in the command string list
        - directory
          the job's working directory
        - environment
          a dictionary with enviroment variables to set/unset (value = None)
        - title
        - show_command_info
          show a message with the full command and job info at the beginning
          of a log.
          If set to a boolean this will override the corresponding Preference
        - input
          an input statement as one out of
          - a filename
          - a filename wrapped in a list
          - a list with an argument (e.g. '-i') and a filename
        - input_file
          an input file.
          If this is not explicitly specified it will be taken from the
          'input' option (or set to an empty string)
        - output/output_file
          corresponding to the input arguments
        - decode_errors
          strategy for handling encoding issues in the communication
          with external processes
        - encoding
          encoding of the process' input and output
        - priority
          The priority the job will have if added to a priority job queue
        - queue
          the name property of a job queue (within app.job_queue()) or None
          by default jobs are added to the 'generic' queue, the other two
          predefined queues are 'engrave' and 'crawler'
        """
        super(Job, self).__init__(parent)
        self._command = command if type(command) == list else [command]
        self.set_input(input)
        self.set_input_file(input_file)
        self.set_output(output)
        self.set_output_file(output_file)
        self._arguments = args or []
        self._directory = directory
        self._environment = {}
        self._success = None
        self._error = None
        self._title = title
        if show_command_info is None:
            s = app.settings('log')
            show_command_info = s.value(
                'show_command_info_on_start', False, bool
            )
        self._show_command_info = show_command_info
        self._runner = None
        self._queue = queue if not no_queue else None
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

    #
    # "Private" methods
    #

    def _abort_message(self):
        """Called by abort().

        Outputs a message that the process has been aborted.

        """
        name = self.display_title()
        self._message(_("Aborting {job}...").format(job=name), NEUTRAL)

    def _bye(self, success):
        """(internal) Ends and emits the done() signal."""
        self._elapsed = time.time() - self._starttime
        if not success:
            self._error = self._process.error()
        self._success = success
        self._process.deleteLater()
        self._process = None
        self.done(success)

    def _cmd_add_arguments(self):
        """
        Add the arguments to the command, if present.
        Serialize tuples/lists if necessary.
        """
        self._command.extend(self.arguments())

    def _cmd_add_input(self):
        """
        Add the input file or the input argument pair
        to the command, if present.
        """
        self._command.extend(self._input or self._input_file)

    def _cmd_add_output(self):
        """
        Add the output file or the output argument pair
        to the command, if present.
        """
        self._command.extend(self._output or self._output_file)

    def _configure_command(self):
        """Process the command if necessary.

        Initially the command is the list given upon instantiation.
        The default implementation is to add (if present)
        - arguments
        - input file/argument pair
        - output file/argument pair
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

    def _error_message(self, error):
        """Called when there is an error (by _slot_error()).

        Outputs a message describing the given QProcess.Error.

        """
        if error == QProcess.FailedToStart:
            self._message(_(
                "Could not start {program}.\n"
                "Please check path and permissions.").format(
                    program=self._command[0]
                ),
                FAILURE
            )
        elif error == QProcess.ReadError:
            self._message(_("Could not read from the process."), FAILURE)
        elif self._process.state() == QProcess.NotRunning:
            self._message(_("An unknown error occurred."), FAILURE)

    def _finished(self, exitCode, exitStatus):
        """(internal) Called when the process has finished."""
        self._finish_message(exitCode, exitStatus)
        success = exitCode == 0 and exitStatus == QProcess.NormalExit
        self._bye(success)

    def _finish_message(self, exitCode, exitStatus):
        """Called when the process finishes (by _finished()).

        Outputs a message on completion of the process.

        """
        if exitCode:
            self._message(_(
                "Exited with return code {code}."
            ).format(code=exitCode), FAILURE)
        elif exitStatus:
            self._message(_(
                "Exited with exit status {status}."
            ).format(status=exitStatus), FAILURE)
        else:
            time = elapsed2str(self.elapsed_time())
            self._message(_(
                "Completed successfully in {time}."
            ).format(time=time), SUCCESS)

    def _message(self, text, type=NEUTRAL):
        """
        Output some text as the given type
        (NEUTRAL, SUCCESS, FAILURE, STDOUT or STDERR).
        """
        self.output(text, type)
        self._history.append((text, type))

    def _queue_message(self, q_title):
        """Called by set_queue().

        Outputs a message that and where the job has been enqueued
        (by JobQueue.add_job) if the queue couldn't start it immediately.

        """
        msg = _(
            "Job '{j_title}' enqueued in queue "
            "'{queue}' with priority {priority}."
        ).format(
            j_title=self.display_title(),
            queue=q_title,
            priority=self.priority()
        )
        self._message(msg, NEUTRAL)

    def _readstderr(self):
        """(internal) Called when STDERR can be read."""
        output = self._process.readAllStandardError()
        self._message(
            self._decoder_stderr(output, self._decode_errors)[0], STDERR
        )

    def _readstdout(self):
        """(internal) Called when STDOUT can be read."""
        output = self._process.readAllStandardOutput()
        self._message(
            self._decoder_stdout(output, self._decode_errors)[0], STDOUT
        )

    def _set_process(self, process):
        """Sets a QProcess instance and connects the signals."""
        self._process = process
        if process.parent() is None:
            process.setParent(QCoreApplication.instance())
        process.finished.connect(self._finished)
        process.error.connect(self._slot_error)
        process.readyReadStandardError.connect(self._readstderr)
        process.readyReadStandardOutput.connect(self._readstdout)

    def _slot_error(self, error):
        """(internal) Called when an error occurs."""
        self._error_message(error)
        if self._process.state() == QProcess.NotRunning:
            self._bye(False)

    def _start_message(self):
        """Called by _start().

        Outputs a message that the process has started.

        """
        name = self.display_title()
        self._message(_("Starting {job}...\n").format(job=name), NEUTRAL)
        if self._show_command_info:
            self._message(
                _(
                    "Command: {cmd}\n"
                    "Job Queue (Runner): '{queue}' ({runner})"
                ).format(
                    cmd=' '.join(self._command),
                    queue=self.queue().title(),
                    runner=self.runner().index()
                ),
                NEUTRAL
            )

    def _update_process_environment(self):
        """(internal) initializes the environment for the process."""
        se = QProcessEnvironment.systemEnvironment()
        for k, v in self.environment().items():
            se.remove(k) if v is None else se.insert(k, v)
        self._process.setProcessEnvironment(se)

    #
    # Properties
    #

    def add_argument(self, arg):
        """
        Append an additional command line argument if it is not
        present already.
        arg may either be a single string or a key-value tuple.
        """
        k, v = arg if type(arg) == tuple else (arg, None)
        if k not in self._arguments:
            self._arguments.append(k)
            if v:
                self._arguments.append(v)

    def arguments(self):
        """
        Command arguments/options list.
        Override if arguments should be processed differently,
        returning a string list.
        """
        return self._arguments

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

    def display_title(self):
        """Title to be displayed in messages.

        If no title is set explicitly, return the command name.

        """
        return self._title or os.path.basename(self._command[0])

    def elapsed_time(self):
        """Return how many seconds this process has been running."""
        if self._elapsed:
            return self._elapsed
        elif self._starttime:
            return time.time() - self._starttime
        return 0.0

    def encoding(self):
        return self._encoding

    def set_encoding(self, value):
        self._encoding = value

    def environment(self, key=None):
        """
        Return either one environment variable
        or the whole dictionary (if key=None).
        """
        if key:
            return self._environment.get(key, None)
        else:
            return self._environment

    def set_environment(self, key, value):
        """
        Set a value in a job's environment.
        If value is None the environment variable will be removed
        from the QProcess environment.
        """
        self._environment[key] = value

    def error(self):
        """
        Return the QProcess.ProcessError if the process produce it.
        Before the process has finished this is always None.
        """
        return self._error

    def failed_to_start(self):
        """Return True if the process failed to start.

        (Call this method after the process has finished.)

        """
        return self._error == QProcess.FailedToStart

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

    def input(self):
        """
        Return the input clause, a list with either no element,
        one filename or an argument/filename pair.
        """
        return self._input

    def set_input(self, input):
        self._input = (
            input if type(input) == list
            else [input] if input is not None
            else []
        )

    def input_file(self):
        return self._input_file or ''

    def set_input_file(self, input_file):
        self._input_file = (
            input_file if input_file is not None
            else self._input[-1] if self._input
            else []
        )

    def is_aborted(self):
        """Returns True if the job was aborted by calling abort()."""
        return self._aborted

    def is_queued(self):
        """Returns True if the job is queued but hasn't started."""
        return isinstance(self._queue, queue.JobQueue)

    def is_running(self):
        """Returns True if this job is running."""
        return bool(self._process)

    def output_arg(self):
        """
        Return the output clause, a list with either no element,
        one filename or an argument/filename pair.
        NOTE: the differing method name is because 'output' is
        a job's signal.
        """
        return self._output

    def set_output(self, output):
        self._output = (
            output if type(output) == list
            else [output] if output is not None
            else []
        )

    def output_file(self):
        return self._output_file or ''

    def set_output_file(self, output_file):
        self._output_file = (
            output_file if output_file is not None
            else self._output[-1] if self._output
            else []
        )

    def priority(self):
        return self._priority

    def set_priority(self, value):
        self._priority = value

    def runner(self):
        """
        Return the Runner object job is run within.
        Before and after that this will return None.
        """
        return self._runner

    def set_runner(self, runner):
        """
        Store a reference to a Runner if the job is run within
        a JobQueue.
        """
        self._runner = runner

    def queue(self):
        """
        Return the JobQueue this job has been queued to.
        Before being added to a queue or after being started
        this will return None.
        """
        if isinstance(self._queue, queue.JobQueue):
            return self._queue

    def set_queue(self, q):
        """Set a queue.

        Called by JobQueue.add_job and JobQueue.start.

        """
        self._queue = q
        if isinstance(q, queue.JobQueue):
            self._queue_message(q.title())

    def start_time(self):
        """Return the time this job was started.

        Returns 0.0 when the job has not been started yet.

        """
        return self._starttime

    def stderr(self):
        """Return the standard error of the process as unicode text."""
        return "".join([line[0] for line in self.history(STDERR)])

    def stdout(self):
        """Return the standard output of the process as unicode text."""
        return "".join([line[0] for line in self.history(STDOUT)])

    def success(self):
        """
        Return True if the job has completed, successfully,
        False if it has finished with an error,
        None if it hasn't been finished (or even started) yet.
        """
        return self._success

    def title(self):
        """Return the job title, as set with set_title().

        The title defaults to an empty string.

        """
        return self._title or ''

    def set_title(self, title):
        """Set the title.

        If the title changed, the title_changed(title) signal is emitted.

        """
        old, self._title = self._title, title
        if title != old:
            self.title_changed(title)

    #
    # "Public" methods
    #

    def abort(self):
        """Abort the process."""
        if self._process:
            self._aborted = True
            self._abort_message()
            if os.name == "nt":
                self._process.kill()
            else:
                self._process.terminate()

    def _start(self):
        self._success = None
        self._error = None
        self._aborted = False
        self._history = []
        self._elapsed = 0.0
        self._starttime = time.time()
        if self._process is None:
            self._set_process(QProcess())
        self._process.started.connect(self.started)
        self._start_message()
        if os.path.isdir(self.directory() or ''):
            self._process.setWorkingDirectory(self.directory())
        if self.environment():
            self._update_process_environment()
        self._process.start(self._command[0], self._command[1:])

    def start(self):
        """Enqueues or starts the process.

        If queue has explicitly been set to None the process
        is started immediately, otherwise it is enqueued to
        the corresponding queue.

        """

        self._configure_command()
        if self._queue is None:
            self._start()
            return
        else:
            self._queue = app.job_queue().queue(self._queue)
            self._queue.add_job(self)
