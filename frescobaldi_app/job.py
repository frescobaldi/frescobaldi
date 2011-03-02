# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
A Job runs LilyPond (or another process) and captures the output
to get it later or to have a log follow it.
"""

import codecs
import os
import time

from PyQt4.QtCore import QCoreApplication, QProcess

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
    
    Set the command attribute to a list of strings describing the program and its arguments.
    Set the directory attribute to a working directory.
    The decoder attribute may be set to a decoder function, it defaults to
    codecs.getdecoder('utf-8'). It is used to decode the output from the process
    to python (unicode) strings.
    
    Call start() to start the process.
    The output() signal emits output (stderr or stdout) from the process.
    The done() signal is always emitted when the process has ended.
    The history() method returns all status messages and output so far.
    
    The status messages and output all are in one of five categories:
    STDERR, STDOUT (output from the process) or NEUTRAL, FAILURE or SUCCESS
    (status messages). When displaying these messages in a log, it is advised
    to take special care for newlines, esp when a status message is displayed.
    Status messages normally have no newlines, so you must add them if needed,
    while output coming from the process may continue in the same line.
    
    """
    output = signals.Signal()
    done = signals.Signal()
    
    def __init__(self):
        self.command = []
        self.directory = ""
        self.decoder = codecs.getdecoder("utf-8")
        
        self._process = None
        self._history = []
        self._starttime = 0.0
        self._elapsed = 0.0
    
    def start(self):
        """Starts the process."""
        self._history = []
        self._elapsed = 0.0
        self._starttime = time.time()
        if self._process is None:
            self.setProcess(QProcess())
        self.startMessage()
        if os.path.isdir(self.directory):
            self._process.setWorkingDirectory(self.directory)
        self._process.start(self.command[0], self.command[1:])
    
    def elapsed(self):
        """Returns how many seconds this process has been running."""
        if self._elapsed:
            return self._elapsed
        elif self._starttime:
            return time.time() - self._starttime
        return 0.0

    def abort(self):
        """Aborts the process."""
        if self._process:
            self._process.terminate()
    
    def isRunning(self):
        """Returns True if this job is running."""
        return bool(self._process)
        
    def setProcess(self, process):
        """Sets a QProcess instance and connects the signals."""
        self._process = process
        if process.parent() is None:
            process.setParent(QCoreApplication.instance())
        process.finished.connect(self._finished)
        process.error.connect(self._error)
        process.readyReadStandardError.connect(self._readstderr)
        process.readyReadStandardOutput.connect(self._readstdout)
    
    def message(self, text, type=NEUTRAL):
        """Outputs some text as the given type (NEUTRAL, SUCCESS, FAILURE, STDOUT or STDERR)."""
        self.output(text, type)
        self._history.append((text, type))
        
    def history(self, types=ALL):
        """Yields the output messages as two-tuples (text, type) since the process started.
        
        If types is given, it should be an OR-ed combination of the status types
        STDERR, STDOUT, NEUTRAL, SUCCESS or FAILURE.
        
        """
        for msg, type in self._history:
            if type & types:
                yield msg, type
        
    def _finished(self, exitCode, exitStatus):
        """Called when the process has finished."""
        self.finishMessage(exitCode, exitStatus)
        success = exitCode == 0 and exitStatus == QProcess.NormalExit
        self._bye(success)
        
    def _error(self, error):
        """Called when an error occurs."""
        self.errorMessage(error)
        if self._process.state() == QProcess.NotRunning:
            self._bye(False)
    
    def _bye(self, success):
        """Ends and emits the done() signal."""
        self._elapsed = time.time() - self._starttime
        self._process.deleteLater()
        self._process = None
        self.done(success)
        
    def _readstderr(self):
        """Called when STDERR can be read."""
        output = self._process.readAllStandardError()
        self.message(self.decoder(output)[0], STDERR)
        
    def _readstdout(self):
        """Called when STDOUT can be read."""
        output = self._process.readAllStandardOutput()
        self.message(self.decoder(output)[0], STDOUT)

    def startMessage(self):
        """Outputs a message the process has started."""
        self.message("Starting...", NEUTRAL)
    
    def errorMessage(self, error):
        """Outputs a message describing the given QProcess.Error."""
        if error == QProcess.FailedToStart:
            self.message(_(
                "Could not start {program}.\n"
                "Please check path and permissions.").format(program = self.command[0]), FAILURE)
        elif error == QProcess.ReadError:
            self.message(_("Could not read from the process."), FAILURE)
        elif self._process.state() == QProcess.NotRunning:
            self.message(_("An unknown error occured."), FAILURE)

    def finishMessage(self, exitCode, exitStatus):
        """Outputs a message on completion of the process."""
        if exitCode:
            self.message(_("Exited with return code {code}.").format(code=exitCode), FAILURE)
        elif exitStatus:
            self.message(_("Exited with exit status {status}.").format(status=exitStatus), FAILURE)
        else:
            time = elapsed2str(self.elapsed())
            self.message(_("Completed successfully in {time}.").format(time=time), SUCCESS)



def elapsed2str(seconds):
    """Returns a short display for the given time period (in seconds)."""
    minutes, seconds = divmod(seconds, 60)
    if minutes:
        return "{0:.0f}'{1:.0f}\"".format(minutes, seconds)
    return '{0:.1f}"'.format(seconds)


