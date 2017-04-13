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
Writes MIDI events to a MIDI output.
"""


import contextlib

from . import event


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

    def reset(self):
        """Restores the MIDI output to an initial state.

        Sets the program to 0, the volume to 90 and sends reset_controllers
        messages to all channels.

        """
        self.reset_controllers()
        self.set_main_volume(90)
        self.set_program_change(0)

    def set_main_volume(self, volume, channel=-1):
        channels = range(16) if channel == -1 else (channel,)
        with self.sender() as send:
            for c in channels:
                send(event.ControllerEvent(c, event.MIDI_CTL_MSB_MAIN_VOLUME, volume))

    def set_program_change(self, program, channel=-1):
        channels = range(16) if channel == -1 else (channel,)
        with self.sender() as send:
            for c in channels:
                send(event.ProgramChangeEvent(c, program))

    def reset_controllers(self, channel=-1):
        """Sends an all_notes_off message to a channel.

        If the channel is -1 (the default), sends the message to all channels.

        """
        channels = range(16) if channel == -1 else (channel,)
        with self.sender() as send:
            for c in channels:
                send(event.ControllerEvent(c, event.MIDI_CTL_RESET_CONTROLLERS, 0))

    def all_sounds_off(self, channel=-1):
        """Sends an all_notes_off message to a channel.

        If the channel is -1 (the default), sends the message to all channels.

        """
        channels = range(16) if channel == -1 else (channel,)
        with self.sender() as send:
            for c in channels:
                send(event.ControllerEvent(c, event.MIDI_CTL_ALL_NOTES_OFF, 0))
                send(event.ControllerEvent(c, event.MIDI_CTL_ALL_SOUNDS_OFF, 0))

    def send_events(self, events):
        """Writes the list of events to the output port.

        Each event is one of the event types in event.py
        Implement to do the actual writing.

        """
        pass

    @contextlib.contextmanager
    def sender(self):
        """Returns a context manager to call for each event to send.

        When the context manager exits, the events are sent using the
        send_events() method.

        """
        l = []
        yield l.append
        if l:
            self.send_events(l)


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

    def convert_event(self, e):
        """Returns a list of integers representing a MIDI message from event."""
        t = type(e)
        if t is event.NoteEvent:
            return self.convert_note_event(e)
        elif t is event.PitchBendEvent:
            return self.convert_pitchbend_event(e)
        elif t is event.ProgramChangeEvent:
            return self.convert_programchange_event(e)
        elif t is event.ControllerEvent:
            return self.convert_controller_event(e)

    def convert_note_event(self, e):
        return [e.type * 16 + e.channel, e.note, e.value]

    def convert_programchange_event(self, e):
        return [0xC0 + e.channel, e.number]

    def convert_controller_event(self, e):
        return [0xB0 + e.channel, e.number, e.value]

    def convert_pitchbend_event(self, e):
        return [0xE0 + e.channel, e.value & 0x7F, e.value >> 7]



