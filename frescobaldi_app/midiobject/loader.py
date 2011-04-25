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


"""
Loads a MIDI file using Max M.'s midi package.

The Loader is a subclass of MidiOutStream and stores all information, events etc.
in a MidiObject instance that represents the loaded file.

"""

import midi.MidiOutStream

from . import event
from . import midiobject


class LoaderBase(midi.MidiOutStream.MidiOutStream):
    """Base class for loading a MIDI file from a MidiInStream or file into a MidiObject.
    
    Although the class is usable, no event except the header event is loaded.
    Inherit this class to implement handlers for the events you're interested in.
    
    """
    def __init__(self, midiObject=None):
        super(Loader, self).__init__()
        self.midi = midiObject or midiobject.MidiObject()

    def append(self, ev):
        """Adds the event to our events dict (by absolute time)
        
        The events dict's keys are the absolute time.
        The value is a dict containing a list of event objects for every track number.
        
        """
        evs = self.midi.events().setdefault(self.abs_time(), {}).setdefault(self.get_current_track(), [])
        evs.append(ev)
        
    def header(self, format=0, nTracks=1, division=96):
        self.midi.setMidiFormat(format)
        self.midi.setNumTracks(nTracks)
        self.midi.setDivision(division)
    

class Loader(LoaderBase):
    """Loader class that loads all events from a MidiInStream.
    
    To filter out some events you could inherit this class and define no-op
    methods for the events you're not interested in.
    
    """
    # event handlers
    def note_on(self, channel=0, note=0x40, velocity=0x40):
        self.append(event.NoteOn(channel, note, velocity))
    
    def note_off(self, channel=0, note=0x40, velocity=0x40):
        self.append(event.NoteOff(channel, note, velocity))

    def aftertouch(self, channel=0, note=0x40, velocity=0x40):
        self.append(event.Aftertouch(channel, note, velocity))

    def continuous_controller(self, channel, controller, value):
        self.append(event.ContinuousController(channel, controller, value))

    def patch_change(self, channel, patch):
        self.append(event.PatchChange(channel, patch))

    def channel_pressure(self, channel, pressure):
        self.append(event.ChannelPressure(channel, pressure))

    def pitch_bend(self, channel, value):
        self.append(event.PitchBend(channel, value))

    def system_exclusive(self, data):
        self.append(event.SystemExclusive(data))
    
    def song_position_pointer(self, value):
        self.append(event.SongPositionPointer(value))

    def song_select(self, songNumber):
        self.append(event.SongSelect(songNumber))

    def tuning_request(self):
        self.append(event.TuningRequest())
            
    def midi_time_code(self, msg_type, values):
        self.append(event.MidiTimeCode(msg_type, values))

    def meta_event(self, meta_type, data):
        self.append(event.MetaEvent(meta_type, data))
    
    def end_of_track(self):
        self.append(event.EndOfTrack())

    def sequence_number(self, value):
        self.append(event.SequenceNumber(value))

    def text(self, text):
        self.append(event.Text(text))

    def copyright(self, text):
        self.append(event.Copyright(text))

    def sequence_name(self, text):
        self.append(event.SequenceName(text))

    def instrument_name(self, text):
        self.append(event.InstrumentName(text))

    def lyric(self, text):
        self.append(event.Lyric(text))

    def marker(self, text):
        self.append(event.Marker(text))

    def cuepoint(self, text):
        self.append(event.Cuepoint(text))
    
    def midi_ch_prefix(self, channel):
        self.append(event.MidiChPrefix(channel))

    def midi_port(self, value):
        self.append(event.MidiPort(value))

    def tempo(self, value):
        self.append(event.Tempo(value))

    def smpt_offset(self, hour, minute, second, frame, framePart):
        self.append(event.SmtpOffset(hour, minute, second, frame, framePart))

    def time_signature(self, nn, dd, cc, bb):
        self.append(event.TimeSignature(nn, dd, cc, bb))

    def key_signature(self, sf, mi):
        self.append(event.KeySignature(sf, mi))

    def sequencer_specific(self, data):
        self.append(event.SequenceSpecific(data))
    
    def timing_clock(self):
        self.append(event.TimingClock())

    def song_start(self):
        self.append(event.SongStart())
    
    def song_stop(self):
        self.append(event.SongStop())

    def song_continue(self):
        self.append(event.SongContinue())

    def active_sensing(self):
        self.append(event.ActiveSensing())

    def system_reset(self):
        self.append(event.SystemReset())


