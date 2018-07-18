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

from PyQt5.QtCore import QSettings

from . import abstractjob

class Job(abstractjob.Job):
    """Executes a single Git command, either blocking or non-blocking.

    The output of the command will be stored in the _stdout and _stderr fields,
    run_blocking() will return the data while run() will invoke the finished
    signal, giving the caller the opportunity to retrieve the data.
    """

    # Check if there's an explicit path to the Git executable
    # or fall back to 'git'
    _exe_pref = QSettings().value("helper_applications/git", 'git', str)
    executable = _exe_pref or 'git'

    _vcs_name = 'Git'

    @classmethod
    def version(cls):
        """Return the Git version as a tuple or False if it is not installed"""
        job = cls()
        args = ['--version']
        stdout, _ = job.run_blocking(args)
        if not stdout:
            # obviously Git is not available
            return False
        match = re.match(r'git version (\d+)\.(\d+)\.(\d+)', stdout[0])
        if match:
            # PEP-440 conform git version (major, minor, patch)
            return tuple(int(g) for g in match.groups())
        else:
            # other reason for unexpected result
            return False
        

class JobQueue(abstractjob.JobQueue):
    """GitJobQueue is the command queue manage Job() objects

    You may need this when you want to run some Git commands in order.
    Job() objects in the queue run one after another.  When an error occurrs
    during runing, GitJobQueue will stop running and emits an "errorOccurred"
    signal.
    """
    pass
