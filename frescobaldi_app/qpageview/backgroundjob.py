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
Run jobs in the background, using QThread.
"""

from PyQt5.QtCore import pyqtSignal, Qt, QThread


class Job(QThread):
    """A simple wrapper around QThread.
    
    Before calling start() you should put the work function in the work
    attribute, and an optional finalize function in the finalize attribute.
    
    Or alternatively, inherit from this class and implement run() and finish()
    yourself.
    
    """
    work = None
    finalize = None
    running = False
    result = None
    
    def __init__(self, parent=None):
        """Init ourselves; the parent can be a QObject which will be our parent."""
        super().__init__(parent)
        self.finished.connect(self._slotFinished)
    
    def start(self):
        self.result = None
        self.running = True     # this is more robust than isRunning()
        super().start()
    
    def run(self):
        """Call the work function in the background thread."""
        self.result = self.work()
    
    def finish(self):
        """This slot is called in the main thread when the work is done.
        
        The default implementation calls the finalize function with the result.
        
        """
        if self.finalize:
            self.finalize(self.result)

    def _slotFinished(self):
        self.running = False
        self.finish()
        self.work = None
        self.finalize = None

