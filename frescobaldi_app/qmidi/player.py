# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
A MIDI player for PyQt5.
"""




from PyQt5.QtCore import pyqtSignal, Qt, QThread, QTimer

import midifile.player


class Player(QThread, midifile.player.Player):
    """An implementation of midifile.player.Player using a QThread and QTimer.

    emit signals:

    stateChanged(playing):
        True or False if playing state changes

    time(msec):
        The playing time, emit by default every 1000ms

    beat(measnum, beat, num, den):
        the measure number, beat number, time signature numerator and denom.,
        where 0 = whole note, 1 = half note, 2 = quarter note, etc.

    user(object):
        any user object that might be added to an event

    """
    stateChanged = pyqtSignal(bool)
    time = pyqtSignal(int)
    beat = pyqtSignal(int, int, int, int)
    user = pyqtSignal(object)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        midifile.player.Player.__init__(self)
        self._timer = None

    def run(self):
        self._timer = QTimer(singleShot=True, timerType=Qt.PreciseTimer)
        self._timer.timeout.connect(self.timer_timeout, Qt.DirectConnection)
        self.timer_start_playing()
        self.stateChanged.emit(True)
        if self.exec_():
            self.timer_stop_playing()
        self._timer = None
        self.stateChanged.emit(False)

    def start(self):
        if self.has_events():
            QThread.start(self)

    def stop(self):
        if self.isRunning():
            self.exit(1)
            self.wait()

    def set_position(self, position, offset=0):
        """Overridden because we can't start/stop the timer from the gui thread."""
        playing = self.isRunning()
        if playing:
            self.stop()
        super(Player, self).set_position(position, offset)
        if playing:
            self.start()

    def timer_start(self, msec):
        """Starts the timer to fire once, the specified msec from now."""
        self._timer.start(int(msec))

    def timer_stop(self):
        self._timer.stop()

    def finish_event(self):
        midifile.player.Player.finish_event(self)
        self.exit(0)

    def time_event(self, time):
        self.time.emit(time)

    def beat_event(self, measnum, beat, num, den):
        self.beat.emit(measnum, beat, num, den)

    def user_event(self, obj):
        self.user.emit(obj)


