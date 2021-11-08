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
QProgressBar subclasses.
"""


from PyQt5.QtCore import QTimeLine, QTimer
from PyQt5.QtWidgets import QProgressBar

class TimedProgressBar(QProgressBar):
    """A QProgressBar showing a certain time elapse."""

    def __init__(
        self,
        parent=None,
        hideWhileIdle=True,
        hidden=False,
        showFinished=3000
    ):
        super(TimedProgressBar, self).__init__(parent, minimum=0, maximum=100)
        self._hideWhileIdle = hideWhileIdle
        self._hidden = hidden
        self._showFinished = showFinished
        self._timeline = QTimeLine(
            updateInterval=100, frameChanged=self.setValue
        )
        self._timeline.setFrameRange(0, 100)
        self._hideTimer = QTimer(
            timeout=self._done,
            singleShot=True,
            interval=showFinished
        )
        if not hidden and not hideWhileIdle:
            self.show()

    def setHidden(self, state):
        self._hidden = state
        self._done()

    def setHideWhileIdle(self, state):
        self._hideWhileIdle = state
        self._done()

    def setShowFinished(self, state):
        self._showFinished = state

    def start(self, total, elapsed=0.0):
        """Starts showing progress.

        total is the number of seconds (maybe float) the timeline will last,
        elapsed (defaulting to 0) is the value to start with.

        """
        self._hideTimer.stop()
        self._timeline.stop()
        self._timeline.setDuration(int(total * 1000))
        self._timeline.setCurrentTime(int(elapsed * 1000))
        self.setValue(self._timeline.currentFrame())
        self._timeline.resume()
        if self._hideWhileIdle and not self._hidden:
            self.show()

    def stop(self):
        """Ends the progress display.

        If showFinished is True (the default), 100% is shown for a few
        seconds and then the progress is reset.
        The progressbar is hidden if the hideOnTimeout attribute is True.

        """
        self._hideTimer.stop()
        self._timeline.stop()
        if self._showFinished and self._hideWhileIdle and not self._hidden:
            self.setValue(100)
            self._hideTimer.start()
        else:
            self._done()

    def _done(self):
        if self._hideWhileIdle and not self._hidden:
            self.hide()
        self.reset()
