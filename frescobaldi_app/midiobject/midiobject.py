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
A MidiObject() represents a loaded MIDI file.
"""

import midi.MidiOutStream

from . import event

class MidiObject(midi.MidiOutStream.MidiOutStream):
    """Represents a MIDI file."""
    def __init__(self):
        super(MidiObject, self).__init__()
        self._events = {}
    
    def append(self, ev):
        """Adds the event to our events dict (by absolute time)"""
        evs = self._events.setdefault(self.abs_time(), [])
        evs.append(ev)
        
    def note_on(self, channel=0, note=0x40, velocity=0x40):
        self.append(event.NoteOn(channel, note, velocity))
    
    def note_off(self, channel=0, note=0x40, velocity=0x40):
        self.append(event.NoteOff(channel, note, velocity))

