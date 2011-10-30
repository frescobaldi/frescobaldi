#! python

# Python midisong.py -- structure for songs in MIDI files.
# Copyright (C) 2011 by Wilbert Berendsen
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
midisong.py -- structures MIDI file data as a song.
"""

import collections

import midiparser


def load(filename):
    """Convenience function to instantiate a Song from a filename.
    
    If the filename is a type 2 MIDI file, just returns the first track.
    
    """
    fmt, div, tracks = midiparser.parse_midi_data(open(filename, 'rb').read())
    if fmt == 2:
        tracks = tracks[:1]
    return Song(div, tracks)


def events_dict(tracks):
    """Returns all events from the track grouped per and mapped to time-step.
    
    every time step has a dictionary with the events per track at that time.
    
    """
    d = collections.defaultdict(dict)
    for n, track in enumerate(tracks):
        for time, evs in midiparser.time_events_grouped(
                midiparser.parse_midi_events(track)):
            d[time][n] = evs
    return d


def events_dict_together(tracks):
    """Returns all events from the track grouped per and mapped to time-step.
    
    every time step has a list with all the events at that time.
    
    """
    d = collections.defaultdict(list)
    for track in tracks:
        for time, evs in midiparser.time_events_grouped(
                midiparser.parse_midi_events(track)):
            d[time].extent(evs)
    return d


def is_tempo(e):
    """Returns True if the event is a Set Tempo Meta-event."""
    return isinstance(e, midiparser.MetaEvent) and e.type == 0x51


def get_tempo(e):
    """Returns the tempo from the Set Tempo Meta-event."""
    return ord(e.data[0])*65536 + ord(e.data[1])*256 + ord(e.data[2])


def smpte_division(div):
    """Converts a MIDI header division from a SMPTE type, if necessary."""
    if div & 0x8000:
        frames = 256 - (div >> 8)
        resolution = div & 0xFF
        div = frames * resolution
    return div


def tempo_map(d, division):
    """Yields two-tuples(time, events).
    
    d should be a dictionary that maps MIDI times to lists or dicts (with a list
    per track) of events. The division is from the MIDI header.
    
    The returned time is in milliseconds, although internally this function
    uses microseconds for exactness. The events are returned unchanged.
    Set Tempo meta-events are correctly interpreted, also in the middle of the
    piece.
    
    """
    # SMPTE division?
    division = smpte_division(division)
    # are the events one list (single-track) or a dict (per-track)?
    for k in d:
        if isinstance(d[k], dict):
            def events(evs):
                for k in sorted(evs):
                    for e in evs[k]:
                        yield e
        else:
            def events(evs):
                return evs
        break
    else:
        return # no events at all
    tempo = 500000  # 120 BPM; 500000 microseconds per beat
    real_time = 0
    last_midi_time = 0
    last_real_time = 0
    for midi_time, evs in sorted(d.items()):
        real_time = last_real_time + (
            (midi_time - last_midi_time) * tempo // division)
        for e in events(evs):
            if is_tempo(e):
                tempo = get_tempo(e)
                last_midi_time = midi_time
                last_real_time = real_time
                break
        yield real_time // 1000, evs


class Song(object):
    """A loaded MIDI file.
    
    The following instance attributes are set on init:
    
    division: the division set in the MIDI header
    ntracks: the number of tracks
    events: a list of two tuples(time, events), where time is the real time in
            milliseconds, and events a dict with per-track lists of events.
    length: the length in milliseconds of the song (same as the time of the last
            event).
    
    """
    def __init__(self, division, tracks):
        """Initialize the Song with the given division and track chunks."""
        self.division = division
        self.ntracks = len(tracks)
        self.events = list(tempo_map(events_dict(tracks), division))
        self.length = self.events[-1][0]




