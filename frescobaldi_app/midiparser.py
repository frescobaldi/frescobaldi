#! python

# Python midiparser.py -- parses MIDI files.
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
midiparser.py -- parses MIDI file data.

This is a simple module that can parse data from a MIDI file and
its tracks.

A basic event handler returns the MIDI events as simple named tuples,
but you can subclass the event handler for more sophisticated behaviour.

Runs with Python 2.5, 2.6, 2.7 and probably also 3.x

"""

import collections
import struct


unpack_midi_header = struct.Struct('>ihhh').unpack
unpack_int = struct.Struct('>i').unpack


MetaEvent = collections.namedtuple('MetaEvent', 'type data')
SysExEvent = collections.namedtuple('SysExEvent', 'type data')
NoteEvent = collections.namedtuple('NoteEvent', 'type channel note value')
ControllerEvent = collections.namedtuple('ControllerEvent', 'channel number value')
ProgramChangeEvent = collections.namedtuple('ProgramChangeEvent', 'channel number')
ChannelAfterTouchEvent = collections.namedtuple('ChannelAfterTouchEvent', 'channel value')
PitchBendEvent = collections.namedtuple('PitchBendEvent', 'channel value')


class EventHandler(object):
    """Handlers for parsed MIDI events.
    
    The default methods return namedtuple objects.
    
    """
    def note_event(self, ev_type, channel, note, value):
        """Called for NoteOn, NoteOff and AfterTouch events."""
        return NoteEvent(ev_type, channel, note, value)
    
    def controller_event(self, channel, number, value):
        """Called for a controller change event."""
        return ControllerEvent(channel, number, value)
    
    def programchange_event(self, channel, number):
        """Called for a program change event."""
        return ProgramChangeEvent(channel, number)
    
    def channelaftertouch_event(self, channel, value):
        """Called for a channel aftertouch event."""
        return ChannelAfterTouchEvent(channel, value)
    
    def pitchbend_event(self, channel, value):
        """Called for a pitch bend event."""
        return PitchBendEvent(channel, value)

    def sysex_event(self, status, data):
        """Called for a SysEx event (F0 - FE)."""
        return SysExEvent(status, data)
    
    def meta_event(self, ev_type, data):
        """Called for a meta event (FF)."""
        return MetaEvent(ev_type, data)


def parse_midi_data(s):
    """Parses MIDI file data from the bytes string s.
    
    Returns a three tuple (format_type, time_division, tracks).
    Every track is an unparsed bytes string.
    
    May raise ValueError or IndexError in case of invalid MIDI data.
    
    """
    if s[:4] != b'MThd':
        raise ValueError("invalid midi data")
    size, fmt, ntracks, division = unpack_midi_header(s[4:14])
    
    pos = size + 8
    
    tracks = []
    for i in range(ntracks):
        if s[pos:pos+4] != b'MTrk':
            raise ValueError("invalid midi track data")
        size, = unpack_int(s[pos+4:pos+8])
        tracks.append(s[pos+8:pos+8+size])
        pos += size + 8
    return fmt, division, tracks


def read_var_len(s, pos):
    """Reads variable-length integer from s starting on pos.
    
    Returns the value and the new position.
    
    """
    value = 0
    while True:
        i = ord(s[pos])
        pos += 1
        value = value * 128 + (i & 0x7F)
        if not i & 0x80:
            return value, pos


def parse_midi_events(s, handler=None):
    """Parses the bytes string s (typically a track) for MIDI events.
    
    If handler is given, it should be an EventHandler instance that
    returns objects describing the event.
    
    Yields two-tuples (delta, event).
    
    """
    if handler is None:
        handler = EventHandler()
        
    running_status = None
    
    pos = 0
    while pos < len(s):
        
        delta, pos = read_var_len(s, pos)
        
        status = ord(s[pos])
        if not status & 0x80:
            status = running_status
        else:
            running_status = status
            pos += 1
        
        if status == 0xFF:
            # meta event
            meta_type = ord(s[pos])
            meta_size, pos = read_var_len(s, pos+1)
            meta_data = s[pos:pos+meta_size]
            pos += meta_size
            ev = handler.meta_event(meta_type, meta_data)
        elif status >= 0xF0:
            # some sort of sysex
            sysex_size, pos = read_var_len(s, pos)
            sysex_data = s[pos:pos+sysex_size]
            pos += sysex_size
            ev = handler.sysex_event(status, sysex_data)
        else:
            # normal channel/voice event
            channel = status & 0xF
            event_type = status >> 4
            if event_type <= 0xA:
                # note on, off or aftertouch
                note = ord(s[pos])
                value = ord(s[pos+1])
                pos += 2
                ev = handler.note_event(event_type, channel, note, value)
            elif event_type == 0xB:
                # Controller
                number = ord(s[pos])
                value = ord(s[pos+1])
                pos += 2
                ev = handler.controller_event(channel, number, value)
            elif event_type == 0xC:
                # Program Change
                number = ord(s[pos])
                pos += 1
                ev = handler.programchange_event(channel, number)
            elif event_type == 0xD:
                # Channel AfterTouch
                value = ord(s[pos])
                pos += 1
                ev = handler.channelaftertouch_event(channel, value)
            else: #event_type == 0xE:
                # Pitch Bend
                value = ord(s[pos]) + ord(s[pos+1]) * 128
                pos += 2
                ev = handler.pitchbend_event(channel, value)
        yield delta, ev


