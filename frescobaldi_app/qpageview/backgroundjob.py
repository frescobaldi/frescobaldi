# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
Run jobs in the background using QThread.
"""


from PyQt5.QtCore import QThread

# as soon as a Job start()s, it is saved here, to prevent it being
# destroyed while running
_runningJobs = set()



class Job(QThread):
    """A simple wrapper around QThread.

    Before calling start() you should put the work function in the work
    attribute, and an optional finalize function (which will be called with the
    result) in the finalize attribute.

    Or alternatively, inherit from this class and implement work() and finish()
    yourself. The result of the work function is stored in the result attribute.

    """
    finalize = None
    running = False
    done = False
    result = None

    def __init__(self, parent=None):
        """Init ourselves; the parent can be a QObject which will be our parent."""
        super().__init__(parent)
        self.finished.connect(self._slotFinished)

    def start(self):
        self.result = None
        self.running = True     # this is more robust than isRunning()
        self.done = False
        _runningJobs.add(self)
        super().start()

    def run(self):
        """Call the work function in the background thread."""
        self.result = self.work()

    def work(self):
        """Implement this to get the work done.
        
        If you have long tasks you can Qt's isInterruptionRequested()
        functionality.
        
        Instead of implementing this method, you can put the work function in
        the work instance attribute.
        
        """
        pass

    def finish(self):
        """This slot is called in the main thread when the work is done.

        The default implementation calls the finalize function with the result.

        """
        if self.finalize:
            self.finalize(self.result)

    def _slotFinished(self):
        _runningJobs.discard(self)
        self.running = False
        self.done = True
        self.finish()


def run(func, callback=None):
    """Run specified function in a background thread.
    
    The thread is immediately started. If a callback is specified, it is called
    in the main thread with the result when the function is ready.
    
    """
    j = Job()
    j.work = func
    j.finalize = callback
    j.start()


