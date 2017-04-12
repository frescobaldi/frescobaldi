# Python midifile package -- parse, load and play MIDI files.
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
A MIDI Player.
"""


import collections
import time
import threading

from . import song


class Player(object):
    """The base class for a MIDI player.

    Use set_output() to set a MIDI output instance (see output.py).
    You can override: timer_midi_time(), timer_start() and timer_stop()
    to use another timing source than the Python threading.Timer instances.

    """
    def __init__(self):
        self._song = None
        self._events = []
        self._position = 0
        self._offset = 0
        self._sync_time = 0
        self._playing = False
        self._tempo_factor = 1.0
        self._output = None
        self._last_exception = None

    def set_output(self, output):
        """Sets an Output instance that handles the MIDI events.

        Use None to disable all output.

        """
        self._output = output

    def output(self):
        """Returns the currently set Output instance."""
        return self._output

    def load(self, filename, time=1000, beat=True):
        """Convenience function, loads a MIDI file.

        See set_song() for the other arguments.

        """
        self.set_song(song.load(filename), time, beat)

    def set_song(self, song, time=1000, beat=True):
        """Loads the specified Song (see song.py).

        If time is not None, it specifies at which interval (in msec) the
        time() method will be called. Default: 1000.
        If beat is True (default), the beat() method will be called on every
        beat.

        """
        playing = self._playing
        if playing:
            self.timer_stop_playing()
        self._song = song
        self._events = make_event_list(song, time, beat)
        self._position = 0
        self._offset = 0
        if playing:
            self.timer_start_playing()

    def song(self):
        """Returns the current Song."""
        return self._song

    def clear(self):
        """Unloads a loaded Song."""
        if self._playing:
            self.stop()
        self._song = None
        self._events = []
        self._position = 0
        self._offset = 0

    def total_time(self):
        """Returns the length in msec of the current song."""
        if self._events:
            return self._events[-1][0]
        return 0

    def current_time(self):
        """Returns the current time position."""
        if self._position >= len(self._events):
            time = self.total_time()
        else:
            time = self._events[self._position][0]
        if self._playing:
            return time - self.timer_offset()
        return time - self._offset

    def start(self):
        """Starts playing."""
        if self.has_events():
            self.timer_start_playing()

    def stop(self):
        """Stops playing."""
        self.timer_stop_playing()

    def is_playing(self):
        """Returns True if the player is playing, else False."""
        return self._playing

    def set_tempo_factor(self, factor):
        """Sets the tempo factor as a floating point value (1.0 is normal)."""
        self._tempo_factor = float(factor)

    def tempo_factor(self):
        """Returns the tempo factor (by default: 1.0)."""
        return self._tempo_factor

    def seek(self, time):
        """Goes to the specified time (in msec)."""
        pos = 0
        offset = 0
        if time:
            # bisect our way in the events list.
            end = len(self._events)
            while pos < end:
                mid = (pos + end) // 2
                if time > self._events[mid][0]:
                    pos = mid + 1
                else:
                    end = mid
            if pos < len(self._events):
                offset = self._events[pos][0] - time
        self.set_position(pos, offset)

    def seek_measure(self, measnum, beat=1):
        """Goes to the specified measure and beat (beat defaults to 1).

        Returns whether the measure position could be found (True or False).

        """
        result = False
        for i, (t, e) in enumerate(self._events):
            if e.beat:
                if e.beat[0] == measnum:
                    position = i
                    result = True
                    if e.beat[1] >= beat:
                        break
                if e.beat[0] > measnum:
                    break
        if result:
            self.set_position(position)
            return True
        return False

    def set_position(self, position, offset=0):
        """(Private) Goes to the specified position in the internal events list.

        This method is called by seek() and seek_measure().

        """
        old, self._position = self._position, position
        if old != self._position:
            self.position_event(old, self._position)
        if self._playing:
            self.timer_stop()
            self.timer_schedule(offset, False)
        else:
            self._offset = offset

    def has_events(self):
        """Returns True if there are events left to play."""
        return bool(self._events) and self._position < len(self._events)

    def next_event(self):
        """(Private) Handles the current event and advances to the next.

        Returns the time in ms (not adjusted by tempo factor!) before
        next_event should be called again.

        If there is no event to handle anymore, returns 0.
        If this event was the last, calls finish() and returns 0.

        """
        if self.has_events():
            time, event = self._events[self._position]
            self.handle_event(time, event)
            self._position += 1
            if self._position < len(self._events):
                return self._events[self._position][0] - time
        return 0

    def handle_event(self, time, event):
        """(Private) Called for every event."""
        if event.midi:
            self.midi_event(event.midi)
        if event.time:
            self.time_event(time)
        if event.beat:
            self.beat_event(*event.beat)
        if event.user is not None:
            self.user_event(event.user)

    def midi_event(self, midi):
        """(Private) Plays the specified MIDI events.

        The format depends on the way MIDI events are stored in the Song.

        """
        if self._output:
            try:
                self._output.midi_event(midi)
            except BaseException as e:
                self.exception_event(e)

    def time_event(self, msec):
        """(Private) Called on every time update."""

    def user_event(self, obj):
        """(Private) Called when there is a user event."""

    def beat_event(self, measnum, beat, num, den):
        """(Private) Called on every beat."""

    def start_event(self):
        """Called when playback is started."""

    def stop_event(self):
        """Called when playback is stopped by the user."""
        if self._output:
            self._output.all_sounds_off()

    def finish_event(self):
        """Called when a song reaches the end by itself."""

    def position_event(self, old, new):
        """Called when the user seeks and the position changes.

        This means MIDI events are skipped and it might be necessary to
        issue an all notes off command to the MIDI output, or to perform
        program changes.

        The default implementation issues an all_notes_off if the
        player is playing.

        """
        if self._playing and self._output:
            self._output.all_sounds_off()

    def exception_event(self, exception):
        """Called when an exception occurs while writing to a MIDI output.

        The default implementation stores the exception in self._last_exception
        and sets the output to None.

        """
        self._last_exception = exception
        self.set_output(None)

    def timer_midi_time(self):
        """Should return a continuing time value in msec, used while playing.

        The default implementation returns the time in msec from the Python
        time module.

        """
        return int(time.time() * 1000)

    def timer_schedule(self, delay, sync=True):
        """Schedules the upcoming event.

        If sync is False, don't look at the previous synchronisation time.

        """
        msec = delay / self._tempo_factor
        if sync:
            self._sync_time += msec
            msec = self._sync_time - self.timer_midi_time()
        else:
            self._sync_time = self.timer_midi_time() + msec
        self.timer_start(max(0, msec))

    def timer_start(self, msec):
        """Starts the timer to fire once, the specified msec from now."""
        self._timer = None
        self._timer = threading.Timer(msec / 1000.0, self.timer_timeout)
        self._timer.start()

    def timer_stop(self):
        """Stops the timer."""
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def timer_offset(self):
        """Returns the time before the next event.

        This value is only useful while playing.

        """
        return int((self._sync_time - self.timer_midi_time()) * self._tempo_factor)

    def timer_start_playing(self):
        """Starts playing by starting the timer for the first upcoming event."""
        reset = self.current_time() == 0
        self._playing = True
        self.start_event()
        if reset and self._output:
            try:
                self._output.reset()
            except BaseException as e:
                self.exception_event(e)
        self.timer_schedule(self._offset, False)

    def timer_timeout(self):
        """Called when the timer times out.

        Handles an event and schedules the next.
        If the end of a song is reached, calls finish_event()

        """
        offset = self.next_event()
        if offset:
            self.timer_schedule(offset)
        else:
            self._offset = 0
            self._playing = False
            self.finish_event()

    def timer_stop_playing(self):
        self.timer_stop()
        self._offset = self.timer_offset()
        self._playing = False
        self.stop_event()


class Event(object):
    """Any event (MIDI, Time and/or Beat).

    Has three attributes that determine what the Player does:

    time: if True, time_event() is called with the current music time.
    beat: None or (measnum, beat, num, den), then beat_event() is called.
    midi: If not None, midi_event() is called with the midi.
    user: Any object, if not None, user_event() is called with the object.

    """
    __slots__ = ['midi', 'time', 'beat', 'user']
    def __init__(self):
        self.midi = None
        self.time = None
        self.beat = None
        self.user = None

    def __repr__(self):
        l = []
        if self.time:
            l.append('time')
        if self.beat:
            l.append('beat({0}:{1})'.format(self.beat[0], self.beat[1]))
        if self.midi:
            l.append('midi')
        if self.user:
            l.append('user')
        return '<Event ' + ', '.join(l) + '>'


def make_event_list(song, time=None, beat=None):
    """Returns a list of all the events in Song.

    Each item is a two-tuple(time, Event).

    If time is given, a time event is generated every that many microseconds
    If beat is True, beat events are generated as well.
    MIDI events are always created.

    """
    d = collections.defaultdict(Event)

    for t, evs in song.music:
        d[t].midi = evs

    if time:
        for t in range(0, song.length+1, time):
            d[t].time = True

    if beat:
        for i in song.beats:
            d[i[0]].beat = i[1:]

    return [(t, d[t]) for t in sorted(d)]


