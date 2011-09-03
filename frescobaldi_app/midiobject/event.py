# This file is part of the midiobject package.
#
# Copyright (c) 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals


class Event(object):
    """The base type for all MIDI events."""
    def output(self, out):
        """Should write our event to the output event handler."""
        pass
    
    def __repr__(self):
        return "<{0}>".format(self.__class__.__name__)

class ChannelEvent(Event):
    """An event type that must have channel attribute."""
    pass

class NoteEvent(ChannelEvent):
    """A NoteOn or NoteOff event."""
    def __init__(self, channel, pitch, velocity):
        """channel: 0-15; pitch, velocity: 0-127"""
        self.channel = channel
        self.pitch = pitch
        self.velocity = velocity
    
    def __repr__(self):
        return "<{0} ch={1} p={2} v={3}>".format(
            self.__class__.__name__, self.channel, pitch2note(self.pitch), self.velocity)

class NoteOn(NoteEvent):
    def output(self, out):
        return out.note_on(self.channel, self.pitch, self.velocity)
        
class NoteOff(NoteEvent):
    def output(self, out):
        return out.note_off(self.channel, self.pitch, self.velocity)

class Aftertouch(NoteEvent):
    def output(self, out):
        return out.aftertouch(self.channel, self.pitch, self.velocity)

class ContinuousController(ChannelEvent):
    def __init__(self, channel, controller, value):
        """channel: 0-15; controller, value: 0-127"""
        self.channel = channel
        self.controller = controller
        self.value = value

    def output(self, out):
        return out.continuous_controller(self.channel, self.controller, self.value)
    
    def __repr__(self):
        return "<{0} ch={1} c={2} v={3}>".format(
            self.__class__.__name__, self.channel, self.controller, self.value)
        
class PatchChange(ChannelEvent):
    def __init__(self, channel, patch):
        """channel: 0-15; patch: 0-127"""
        self.channel = channel
        self.patch = patch
    
    def output(self, out):
        return out.patch_change(self.channel, self.patch)
    
    def __repr__(self):
        return "<{0} ch={1} patch={2}>".format(
            self.__class__.__name__, self.channel, self.patch)
        
class ChannelPressure(ChannelEvent):
    def __init__(self, channel, pressure):
        """channel: 0-15; pressure: 0-127"""
        self.channel = channel
        self.pressure = pressure
        
    def output(self, out):
        return out.channel_pressure(self.channel, self.pressure)

    def __repr__(self):
        return "<{0} ch={1} pressure={2}>".format(
            self.__class__.__name__, self.channel, self.pressure)
        
class PitchBend(ChannelEvent):
    def __init__(self, channel, value):
        """channel: 0-15; value: 0-16383"""
        self.channel = channel
        self.value = value
        
    def output(self, out):
        return out.pitch_bend(self.channel, self.value)
    
    def __repr__(self):
        return "<{0} ch={1} value={2}>".format(
            self.__class__.__name__, self.channel, self.value)

class SystemExclusive(Event):
    def __init__(self, data):
        self.data = data
        
    def output(self, out):
        return out.system_exclusive(self.data)
    
    def __repr__(self):
        maxlen = 10
        data = " ".join(hex(ord(d))[2:] for d in self.data[:maxlen])
        if len(self.data) > maxlen:
            data += " ..."
        return "<{0} hex:{1}>".format(self.__class__.__name__, data)
        
class SongPositionPointer(Event):
    def __init__(self, value):
        """value: 0-16383"""
        self.value = value
        
    def output(self, out):
        return out.song_position_pointer(self.value)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.value)

class SongSelect(Event):
    def __init__(self, songNumber):
        """songNumber: 0-127"""
        self.songNumber = songNumber
    
    def output(self, out):
        return out.song_select(self.songNumber)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.songNumber)

class TuningRequest(Event):
    def output(self, out):
        return out.tuning_request()

class MidiTimeCode(Event):
    def __init__(self, msg_type, values):
        """msg_type: 0-7; values: 0-15"""
        self.msg_type = msg_type
        self.values = values
    
    def output(self, out):
        return out.midi_time_code(self.msg_type, self.values)
    
    def __repr__(self):
        return "<{0} msg_type={1} values={2}>".format(self.__class__.__name__, self.msg_type, self.values)

class MetaEvent(Event):
    def __init__(self, meta_type, data):
        """Handles any undefined meta events"""
        self.meta_type = meta_type
        self.data = data
    
    def output(self, out):
        return out.meta_event(self.meta_type, self.data)

class SequenceNumber(Event):
    def __init__(self, value):
        """value: 0-16383"""
        self.value = value
    
    def output(self, out):
        return out.sequence_number(self.value)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.value)

class TextEvent(Event):
    """Base class for events with only a text attribute."""
    def __init__(self, text):
        """text: string"""
        self.text = text
    
    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, repr(self.text))

class Text(TextEvent):
    """Text event"""
    def output(self, out):
        return out.text(self.text)

class Copyright(TextEvent):
    """Copyright notice"""
    def output(self, out):
        return out.copyright(self.text)

class SequenceName(TextEvent):
    """Sequence/track name"""
    def output(self, out):
        return out.sequence_name(self.text)

class InstrumentName(TextEvent):
    """Instrument name"""
    def output(self, out):
        return out.instrument_name(self.text)

class Lyric(TextEvent):
    """Lyric"""
    def output(self, out):
        return out.lyric(self.text)

class Marker(TextEvent):
    """Marker"""
    def output(self, out):
        return out.marker(self.text)

class Cuepoint(TextEvent):
    """Cuepoint"""
    def output(self, out):
        return out.cuepoint(self.text)

class MidiChPrefix(ChannelEvent):
    """Midi Channel Prefix event (DEPRECATED)"""
    def __init__(self, channel):
        """channel: midi channel for subsequent data (deprecated in the spec)"""
        self.channel = channel
    
    def output(self, out):
        return out.midi_ch_prefix(self.channel)
        
class MidiPort(Event):
    """Midi Port event (DEPRECATED)"""
    def __init__(self, value):
        """value: Midi port (deprecated in the spec)"""
        self.value = value
    
    def output(self, out):
        return out.midi_port(self.value)
    
    def __repr__(self):
        return "<{0} value={1}>".format(self.__class__.__name__, self.value)

class Tempo(Event):
    """Tempo event"""
    def __init__(self, value):
        """value: 0-2097151 tempo in us/quarternote
        
        (to calculate value from bpm: int(60,000,000.00 / BPM))
        
        """
        self.value = value
        
    def output(self, out):
        return out.tempo(self.value)
    
    def __repr__(self):
        return "<{0} value={1}>".format(self.__class__.__name__, self.value)

class SmptOffset(Event):
    """SMPT Time event"""
    def __init__(self, hour, minute, second, frame, framePart):
        """
        hour,
        minute,
        second: 3 bytes specifying the hour (0-23), minutes (0-59) and 
                seconds (0-59), respectively. The hour should be 
                encoded with the SMPTE format, just as it is in MIDI 
                Time Code.
        frame: A byte specifying the number of frames per second (one 
               of : 24, 25, 29, 30).
        framePart: A byte specifying the number of fractional frames, 
                   in 100ths of a frame (even in SMPTE-based tracks 
                   using a different frame subdivision, defined in the 
                   MThd chunk).
        """
        self.hour = hour
        self.minute = minute
        self.second = second
        self.frame = frame
        self.framePart = framePart
        
    def output(self, out):
        return out.smpt_offset(self.hour, self.minute, self.second, self.frame, self.framePart)

    def __repr__(self):
        return "<{0} {1:02d}:{2:02d}:{3:02d}, {4:02d}-{5:03d}>".format(
            self.__class__.__name__, self.hour, self.minute, self.second, self.frame, self.framePart)

class TimeSignature(Event):
    def __init__(self, nn, dd, cc, bb):
        """
        nn: Numerator of the signature as notated on sheet music
        dd: Denominator of the signature as notated on sheet music
            The denominator is a negative power of 2: 2 = quarter 
            note, 3 = eighth, etc.
        cc: The number of MIDI clocks in a metronome click
        bb: The number of notated 32nd notes in a MIDI quarter note 
            (24 MIDI clocks)        
        """
        self.nn = nn
        self.dd = dd
        self.cc = cc
        self.bb = bb
        
    def output(self, out):
        return out.time_signature(self.nn, self.dd, self.cc, self.bb)
    
    def __repr__(self):
        return "<{0} n={1} d={2} c={3} b={4}".format(
            self.__class__.__name__, self.nn, self.dd, self.cc, self.bb)

class KeySignature(Event):
    def __init__(self, sf, mi):
        """
        sf: is a byte specifying the number of flats (-ve) or sharps 
            (+ve) that identifies the key signature (-7 = 7 flats, -1 
            = 1 flat, 0 = key of C, 1 = 1 sharp, etc).
        mi: is a byte specifying a major (0) or minor (1) key.
        """
        self.sf = sf
        self.mi = mi
    
    def output(self, out):
        return out.key_signature(self.sf, self.mi)
    
    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, keysignature(self.sf, self.mi))

class SequenceSpecific(Event):
    def __init__(self, data):
        """data: the data as byte values"""
        self.data = data
    
    def output(self, out):
        return out.sequence_specific(self.data)

class TimingClock(Event):
    def output(self, out):
        return out.timing_clock()

class SongStart(Event):
    def output(self, out):
        return out.song_start()

class SongStop(Event):
    def output(self, out):
        return out.song_stop()

class SongContinue(Event):
    def output(self, out):
        return out.song_continue()

class ActiveSensing(Event):
    def output(self, out):
        return out.active_sensing()

class SystemReset(Event):
    def output(self, out):
        return out.system_reset()


_notenames = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
_octavenames = [",,,,", ",,,", ",,", ",", "", "'", "''", "'''", "''''", "'''''"]

def pitch2note(p):
    """Returns a notename from the given MIDI pitch, e.g. "c'".
    
    This is only used in the __repr__ functions of note events.
    
    """
    octave, note = divmod(p, 12)
    return _notenames[note]+_octavenames[octave]


def keysignature(sf, mi):
    # negative?
    if sf > 128:
        sf -= 256
    # adjust pitch name for minor
    i = sf + (4 if mi else 1)
    # add accidentals
    accs, pitch = divmod(i, 7)
    suffix = '&' * -accs if accs < 0 else '#' * accs
    return 'fcgdaeb'[pitch] + suffix + (" minor" if mi else " major")

