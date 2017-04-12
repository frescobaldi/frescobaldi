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
midifile.song -- structures MIDI file data as a song.
"""


import collections

from . import event
from . import parser


def load(filename):
    """Convenience function to instantiate a Song from a filename.

    If the filename is a type 2 MIDI file, just returns the first track.

    """
    with open(filename, 'rb') as midifile:
        fmt, div, tracks = parser.parse_midi_data(midifile.read())
    if fmt == 2:
        tracks = tracks[:1]
    return Song(div, tracks)


def events_dict(tracks):
    """Returns all events from the track grouped per and mapped to time-step.

    every time step has a dictionary with the events per track at that time.

    """
    d = collections.defaultdict(dict)
    for n, track in enumerate(tracks):
        for time, evs in parser.time_events_grouped(
                parser.parse_midi_events(track)):
            d[time][n] = evs
    return d


def events_dict_together(tracks):
    """Returns all events from the track grouped per and mapped to time-step.

    every time step has a list with all the events at that time.

    """
    d = collections.defaultdict(list)
    for track in tracks:
        for time, evs in parser.time_events_grouped(
                parser.parse_midi_events(track)):
            d[time].extend(evs)
    return d


def is_tempo(e):
    """Returns True if the event is a Set Tempo Meta-event."""
    return isinstance(e, event.MetaEvent) and e.type == 0x51


def get_tempo(e):
    """Returns the tempo from the Set Tempo Meta-event."""
    return e.data[0]*65536 + e.data[1]*256 + e.data[2]


def is_time_signature(e):
    """Returns True if the event is a Set Time Signature Meta-event."""
    return isinstance(e, event.MetaEvent) and e.type == 0x58


def get_time_signature(e):
    """Returns the num, den, clocks, num_32s from the Time Signature event."""
    return tuple(e.data)


def smpte_division(div):
    """Converts a MIDI header division from a SMPTE type, if necessary."""
    if div & 0x8000:
        frames = 256 - (div >> 8)
        resolution = div & 0xFF
        div = frames * resolution
    return div


def events_iter(d):
    """Return an iterator function over the events in one value of dict d.

    The values in d can be dicts (per-track) or lists (single track).
    Returns None if the events dictionary is empty.

    """
    for k in d:
        return iter_events_dict if isinstance(d[k], dict) else iter


def iter_events_dict(evs):
    """Iter over the (per-track) dictionary's events."""
    for k in sorted(evs):
        for e in evs[k]:
            yield e


class TempoMap(object):
    """Converts midi time to real time in microseconds."""
    def __init__(self, d, division):
        """Initialize our tempo map based on events d and division."""
        # are the events one list (single-track) or a dict (per-track)?
        self.division = smpte_division(division)
        self.times = times = []
        events = events_iter(d)
        if events:
            for midi_time, evs in sorted(d.items()):
                for e in events(evs):
                    if is_tempo(e):
                        times.append((midi_time, get_tempo(e)))
                        break
        if not times or times[0][0] != 0:
            times.insert(0, (0, 500000))

    def real_time(self, midi_time):
        """Returns the real time in microseconds for the given MIDI time."""
        real_time = 0
        times = self.times
        for i in range(1, len(times)):
            if times[i][0] >= midi_time:
                real_time += (midi_time - times[i-1][0]) * times[i-1][1]
                break
            real_time += (times[i][0] - times[i-1][0]) * times[i-1][1]
        else:
            real_time += (midi_time - times[-1][0]) * times[-1][1]
        return real_time // self.division

    def msec(self, midi_time):
        """Returns the real time in milliseconds."""
        return self.real_time(midi_time) // 1000


def beats(d, division):
    """Yields tuples for every beat in the events dictionary d.

    Each tuple is:
        (midi_time, beat_num, beat_total, denominator)

    With this you can easily add measure numbers and find measure positions
    in the MIDI.

    """
    events = events_iter(d)
    if not events:
        return
    time_sigs = []
    times = sorted(d)
    for midi_time in times:
        for e in events(d[midi_time]):
            if is_time_signature(e):
                time_sigs.append((midi_time, get_time_signature(e)))
    if not time_sigs or time_sigs[0][0] != 0:
        # default time signature at start
        time_sigs.insert(0, (0, (4, 4, 24, 8)))

    # now yield a tuple for every beat
    time = 0
    sigs_index = 0
    while time <= times[-1]:

        if sigs_index < len(time_sigs) and time >= time_sigs[sigs_index][0]:
            # new time signature
            time, (num, den, clocks, n32s) = time_sigs[sigs_index]
            step = (4 * division) // (2 ** den)
            beat = 1
            sigs_index += 1

        yield time, beat, num, den
        time += step
        beat = beat % num + 1


class Song(object):
    """A loaded MIDI file.

    The following instance attributes are set on init:

    division: the division set in the MIDI header
    ntracks: the number of tracks
    events: a dict mapping MIDI times to a dict with per-track lists of events.
    tempo_map: TempoMap instance that computes real time from MIDI time.
    length: the length in milliseconds of the song (same as the time of the last
            event).

    beats: a list of tuples(msec, measnum, beat, num, den) for every beat
    music: a list of tuples(msec, d) where d is a dict mapping tracknr to events

    """
    def __init__(self, division, tracks):
        """Initialize the Song with the given division and track chunks."""
        self.division = division
        self.ntracks = len(tracks)
        self.events = events_dict(tracks)
        self.tempo_map = t = TempoMap(self.events, division)
        self.length = t.msec(max(self.events))

        self.beats = b = []
        measnum = 0
        for midi_time, beat, num, den in beats(self.events, division):
            if beat == 1:
                measnum += 1
            b.append((t.msec(midi_time), measnum, beat, num, den))
        self.music = [(t.msec(midi_time), evs)
                      for midi_time, evs in sorted(self.events.items())]

    def beat(self, time):
        """Returns (time, measnum, beat, num, den) for the beat at time."""
        if not self.beats:
            return (0, 0, 0, 4, 2)
        pos = 0
        if time:
            # bisect our way in the beats list.
            end = len(self.beats)
            while pos < end:
                mid = (pos + end) // 2
                if time > self.beats[mid][0]:
                    pos = mid + 1
                else:
                    end = mid
        return self.beats[min(pos, len(self.beats) - 1)]


