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

import midi.MidiInFile

from . import loader


class MidiObject(object):
    """Represents a MIDI file."""
    def __init__(self):
        """Initializes an empty MIDI object."""
        self.clear()
        
    def clear(self):
        """Initializes ourselves as an empty MIDI object."""
        self._format = 1
        self._numTracks = 0
        self._division = 96
        self._events = {}
        
    def load(self, f):
        """Initializes ourselves from a file or file handle."""
        ldr = loader.Loader()
        inp = midi.MidiInFile.MidiInFile(ldr, f)
        inp.read()
        self.initFromLoader(ldr)

    def initFromLoader(self, ldr):
        """Initializes ourselves from the contents of Loader ldr.
        
        Theoretically the MidiObject itself could be a subclass of MidiOutStream
        like the Loader is, but that would leave us with all the unnecessary
        event handler methods once the file is read, which makes the MidiObject
        class more difficult to understand for user-developers.
        
        """
        self._format = ldr._format
        self._numTracks = ldr._numTracks
        self._division = ldr._division
        self._events = ldr._events

    def midiFormat(self):
        return self._format
    
    def numTracks(self):
        return self._numTracks
    
    def division(self):
        return self._division
    
    def events(self):
        """Returns all the MIDI events in a dictionary.
        
        The events dict's keys are the absolute time.
        The value is a dict containing a list of event objects for every track number.
        
        """
        return self._events
        
