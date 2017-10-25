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




class JobQueue(QObject):
    """GitJobQueue is the command queue manage Job() objects

    You may need this when you want to run some Git commands in order.
    Job() objects in the queue run one after another.  When an error occurrs
    during runing, GitJobQueue will stop running and emits an "errorOccurred"
    signal.
    """

    errorOccurred = pyqtSignal(QProcess.ProcessError)

