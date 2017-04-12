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
midifile.parser -- parses MIDI file data.

This is a simple module that can parse data from a MIDI file and
its tracks.

A basic event factory returns the MIDI events as simple named tuples,
but you can subclass the event factory for more sophisticated behaviour.

Runs with Python 2.6, 2.7 and 3.

"""

from __future__ import print_function

import sys
import struct

from . import event


PY2 = sys.version_info[0] == 2


unpack_midi_header = struct.Struct(b'>hhh').unpack
unpack_int = struct.Struct(b'>i').unpack


def get_chunks(s):
    """Splits a MIDI file bytes string into chunks.

    Yields (b'Name', b'data') tuples.

    """
    pos = 0
    while pos < len(s):
        name = s[pos:pos+4]
        size, = unpack_int(s[pos+4:pos+8])
        yield name, s[pos+8:pos+8+size]
        pos += size + 8


def parse_midi_data(s):
    """Parses MIDI file data from the bytes string s.

    Returns a three tuple (format_type, time_division, tracks).
    Every track is an unparsed bytes string.

    May raise ValueError or IndexError in case of invalid MIDI data.

    """
    chunks = get_chunks(s)
    for name, data in chunks:
        if name == b'MThd':
            fmt, ntracks, division = unpack_midi_header(data[:6])
            tracks = [data for name, data in chunks if name == b'MTrk']
            return fmt, division, tracks
        break
    raise ValueError("invalid midi data")


def read_var_len(s, pos):
    """Reads variable-length integer from byte string s starting on pos.

    Returns the value and the new position.

    """
    value = 0
    while True:
        i = s[pos]
        pos += 1
        value = value * 128 + (i & 0x7F)
        if not i & 0x80:
            return value, pos


def parse_midi_events(s, factory=None):
    """Parses the bytes string s (typically a track) for MIDI events.

    If factory is given, it should be an EventFactory instance that
    returns objects describing the event.

    Yields two-tuples (delta, event).

    Raises ValueError or IndexError on invalid MIDI data.

    """
    if factory is None:
        factory = event.EventFactory()

    running_status = None

    if PY2:
        s = bytearray(s)

    pos = 0
    while pos < len(s):

        delta, pos = read_var_len(s, pos)

        status = s[pos]
        if status & 0x80:
            running_status = status
            pos += 1
        elif not running_status:
            raise ValueError("invalid running status")
        else:
            status = running_status

        ev_type = status >> 4
        channel = status & 0x0F

        if ev_type <= 0x0A:
            # note on, off or aftertouch
            note = s[pos]
            value = s[pos+1]
            pos += 2
            ev = factory.note_event(ev_type, channel, note, value)
        elif ev_type >= 0x0F:
            running_status = None
            if status == 0xFF:
                # meta event
                meta_type = s[pos]
                meta_size, pos = read_var_len(s, pos+1)
                meta_data = s[pos:pos+meta_size]
                pos += meta_size
                ev = factory.meta_event(meta_type, meta_data)
            else:
                # some sort of sysex
                sysex_size, pos = read_var_len(s, pos)
                sysex_data = s[pos:pos+sysex_size]
                pos += sysex_size
                ev = factory.sysex_event(status, sysex_data)
        elif ev_type == 0x0E:
            # Pitch Bend
            value = s[pos] + s[pos+1] * 128
            pos += 2
            ev = factory.pitchbend_event(channel, value)
        elif ev_type == 0xD:
            # Channel AfterTouch
            value = s[pos]
            pos += 1
            ev = factory.channelaftertouch_event(channel, value)
        elif ev_type == 0xB:
            # Controller
            number = s[pos]
            value = s[pos+1]
            pos += 2
            ev = factory.controller_event(channel, number, value)
        else: # ev_type == 0xC
            # Program Change
            number = s[pos]
            pos += 1
            ev = factory.programchange_event(channel, number)
        yield delta, ev


def time_events(track, time=0):
    """Yields two-tuples (time, event).

    The track is the generator returned by parse_midi_events,
    the time is accumulated from the given starting time (defaulting to 0).

    """
    for delta, ev in track:
        time += delta
        yield time, ev


def time_events_grouped(track, time=0):
    """Yields two-tuples (time, event_list).

    Every event_list is a Python list of all events happening on that time.
    The track is the generator returned by parse_midi_events,
    the time is accumulated from the given starting time (defaulting to 0).

    """
    evs = []
    for delta, ev in track:
        if delta:
            if evs:
                yield time, evs
                evs = []
            time += delta
        evs.append(ev)
    if evs:
        yield time, evs



if __name__ == '__main__':
    """Test specified MIDI files."""
    import sys
    files = sys.argv[1:]
    for f in files:
        with open(f, 'rb') as midifile:
            s = midifile.read()
        ftm, div, tracks = parse_midi_data(s)
        try:
            for t in tracks:
                print(list(parse_midi_events(t)))
        except Exception as e:
            print('error in:', f)
            print(e)



