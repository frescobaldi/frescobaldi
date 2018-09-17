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
A (multithreaded) Job queue
"""

#NOTE/TODO: For now this module contains only the Scheduler class that
# had been provided by process.py. The Scheduler has to be replaced by a
# JobQueue class, and the single use in lilypondinfo.py adjusted accordingly.

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
