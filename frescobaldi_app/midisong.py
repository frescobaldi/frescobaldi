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


def tempo_map(d, division):
    """Returns a list of two-tuples(time, events)."""
    tempo = 500000  # 120 BPM
    real_time = 0
    last_midi_time = 0
    last_real_time = 0
    for midi_time, evs in sorted(d.items()):
        real_time = last_real_time + (
            (midi_time - last_midi_time) * tempo / division)
        if 0: # new_tempo:
            tempo = new_tempo
            last_midi_time = midi_time
            last_real_time = real_time
        yield real_time, evs
        

class Song(object):
    def __init__(self, division, tracks):
        self.division = division
        
        self.ntracks = len(tracks)
        self.events = events_dict(tracks)
        

