#! python

# Python midiplayer.py -- base class for a MIDI player
# Copyright (C) 2011 by Wilbert Berendsen
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

import time
import threading

import collections
import midisong


class Player(object):
    """The base class for a MIDI player.
    
    It should be inherited to actually play MIDI:
    - midi_event() should be implemented to play the MIDI to an output port.
    - stop_event() to maybe shut off all notes
    - position_event() for the same reason
    You can also override: timer_midi_time(), timer_start() and timer_stop()
    to use another timing source than the Python threading.Timer instances.
    
    """
    def __init__(self):
        self._song = None
        self._events = []
        self._position = 0
        self._offset = 0
        self._target = 0
        self._playing = False
        self._tempo_factor = 1.0
    
    def load(self, filename, time=1000, beat=True):
        """Convenience function, loads a MIDI file.
        
        See setSong() for the other arguments.
        
        """
        song = midisong.load(filename)
        self.set_song(song, time, beat)
    
    def set_song(self, song, time=1000, beat=True):
        """Loads the specified Song (see midisong.py).
        
        If time is not None, it specifies at which interval (in msec) the
        time() method will be called. Default: 1000.
        If beat is True (default), the beat() method will be called on every
        beat.
        
        """
        self._song = song
        self._events = make_event_list(song, time, beat)
    
    def song(self):
        """Returns the current Song."""
        return self._song
    
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
        self.timer_start_playing()
        
    def stop(self):
        """Stops playing."""
        self.timer_stop_playing()
    
    def is_playing(self):
        """Returns True if the player is playing, else False."""
        return self._playing
    
    def set_tempo_factor(self, factor):
        """Sets the tempo factor as a floating point value (1.0 is normal)."""
        factor = float(factor)
        if factor == self._tempo_factor:
            return
        if self._playing:
            self.timer_stop()
            offset = self.timer_offset()
            self._tempo_factor = factor
            self.timer_schedule(offset)
        else:
            self._tempo_factor = factor
    
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
        
        The default implementation does nothing with the time offset,
        but inherited implementations may wait that many msec before
        triggering the event at that position.
        
        This method is called by seek() and seek_measure().
        
        """
        old, self._position = self._position, position
        if self._playing:
            self._stop_timer()
            if old != self._position
                self.position_event(old, self._position)
            self._schedule_next(offset)
        else:
            self._offset = offset
        
    def next_event(self):
        """(Private) Handles the current event and advances to the next.
        
        Returns the time in ms (not adjusted by tempo factor!) before
        next_event should be called again.
        
        If there is no event to handle anymore, returns 0.
        If this event was the last, calls finish() and returns 0.
        
        """
        if self._events and self._position < len(self._events):
            time, event = self._events[self._position]
            self.handle_event(time, event)
            self._position += 1
            if self._position < len(self._events):
                return self._events[self._position][0] - time
        return 0
    
    def handle_event(self, time, event):
        """(Private) Called for every event."""
        print event # DEBUG
        if event.midi:
            self.midi_event(event.midi)
        if event.time:
            self.time_event(time)
        if event.beat:
            self.beat_event(*event.beat)
    
    def midi_event(self, midi):
        """(Private) Plays the specified MIDI events.
        
        The format depends on the way MIDI events are stored in the Song.
        
        """
    
    def time_event(self, msec):
        """(Private) Called on every time update."""
    
    def beat_event(self, measnum, beat, num, den):
        """(Private) Called on every beat."""
    
    def start_event(self):
        """Called when playback is started."""
    
    def stop_event(self):
        """Called when playback is stopped by the user."""
        
    def finish_event(self):
        """Called when a song reaches the end by itself."""
    
    def position_event(self, old, new):
        """Called when the user seeks while playing and the position changes.
        
        This means MIDI events are skipped and it might be necessary to 
        issue an all notes off command to the MIDI output.
        
        """
        
    def timer_midi_time(self):
        """Should return a continuing time value in msec, used while playing.
        
        The default implementation returns the time in msec from the Python
        time module.
        
        """
        return int(time.time() * 1000)
    
    def timer_schedule(self, delay):
        """Schedules the upcoming event."""
        msec = delay / self._tempo_factor
        self._target += msec
        real_delay = self._target - self.timer_midi_time()
        self.timer_start(real_delay)
    
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
        return int((self._target - self.timer_midi_time()) * self._tempo_factor)
    
    def timer_start_playing(self):
        """Starts playing by starting the timer for the first upcoming event."""
        self._playing = True
        self._target = self.timer_midi_time()
        self.start_event()
        if self._offset:
            self.timer_schedule(self._offset)
        else:
            self.timer_timeout()
    
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
    
    time: if True, time_event() is caled with the current music time.
    beat: None or (measnum, beat, num, den), then beat_event() is called.
    midi: If not None, midi_event() is called with the midi.
    
    """
    __slots__ = ['midi', 'time', 'beat']
    def __init__(self):
        self.midi = None
        self.time = None
        self.beat = None

    def __repr__(self):
        l = []
        if self.time:
            l.append('time')
        if self.beat:
            l.append('beat({0}:{1})'.format(self.beat[0], self.beat[1]))
        if self.midi:
            l.append('midi')
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


