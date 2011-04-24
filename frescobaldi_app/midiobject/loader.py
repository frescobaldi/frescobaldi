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
This information is then transferred to a MidiObject instance that represents the loaded file.
"""

import midi.MidiOutStream

from . import event

class Loader(midi.MidiOutStream.MidiOutStream):
    def __init__(self):
        super(Loader, self).__init__()
        self._events = {}

    def append(self, ev):
        """Adds the event to our events dict (by absolute time)
        
        The events dict's keys are the absolute time.
        The value is a dict containing a list of event objects for every track number.
        
        """
        evs = self._events.setdefault(self.abs_time(), {}).setdefault(self.get_current_track(), [])
        evs.append(ev)
        
    # event handlers
    def header(self, format=0, nTracks=1, division=96):
        self._format = format
        self._numTracks = nTracks
        self._division = division
    
    def note_on(self, channel=0, note=0x40, velocity=0x40):
        self.append(event.NoteOn(channel, note, velocity))
    
    def note_off(self, channel=0, note=0x40, velocity=0x40):
        self.append(event.NoteOff(channel, note, velocity))

