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
Writes MIDI events to a MIDI output.
"""

import midiparser

MIDI_CTL_ALL_SOUNDS_OFF = 0x78
MIDI_CTL_ALL_NOTES_OFF  = 0x7B

class Output(object):
    """Abstract base class for a MIDI output.
    
    Inherit to implement the actual writing to MIDI ports.
    The midiplayer.Player calls midi_event and all_notes_off.
    
    """
    
    def midi_event(self, midi):
        """Handles a list or dict of MIDI events from a Song (midisong.py)."""
        if isinstance(midi, dict):
            # dict mapping track to events?
            midi = sum(map(midi.get, sorted(midi)), [])
        self.send_events(midi)
    
    def all_sounds_off(self, channel=-1):
        """Sends an all_notes_off message to a channel.
        
        If the channel is -1 (the default), sends the message to all channels.
        
        """
        l = []
        channels = range(16) if channel == -1 else (channel,)
        for c in channels:
            l.append(midiparser.ControllerEvent(c, MIDI_CTL_ALL_NOTES_OFF, 0))
            l.append(midiparser.ControllerEvent(c, MIDI_CTL_ALL_SOUNDS_OFF, 0))
        self.send_events(l)
        
    def send_events(self, events):
        """Writes the list of events to the output port.
        
        Each event is one of the event types in midiparser.py
        Implement to do the actual writing.
        
        """
        pass


class PortMidiOutput(Output):
    """Writes events to a PortMIDI Output instance.
    
    The PortMIDI Output instance should be in the output attribute.
    
    """
    output = None
    
    def send_events(self, events):
        """Writes the list of events to the PortMIDI output port."""
        l = []
        for e in events:
            m = self.convert_event(e)
            if m:
                l.append([m, 0])
        while len(l) > 1024:
            self.output.write(l[:1024])
            l = l[1024:]
        if l:
            self.output.write(l)
    
    def convert_event(self, event):
        """Returns a list of integers representing a MIDI message from event."""
        t = type(event)
        if t is midiparser.NoteEvent:
            return self.convert_note_event(event)
        elif t is midiparser.PitchBendEvent:
            return self.convert_pitchbend_event(event)
        elif t is midiparser.ProgramChangeEvent:
            return self.convert_programchange_event(event)
        elif t is midiparser.ControllerEvent:
            return self.convert_controller_event(event)
    
    def convert_note_event(self, event):
        return [event.type * 16 + event.channel, event.note, event.value]

    def convert_programchange_event(self, event):
        return [0xC0 + event.channel, event.value]

    def convert_controller_event(self, event):
        return [0xB0 + event.channel, event.number, event.value]

    def convert_pitchbend_event(self, event):
        return [0xE0 + event.channel, event.value & 0x7F, event.value >> 7]



