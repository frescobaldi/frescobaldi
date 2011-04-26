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

import midi.MidiOutFile # used for saving


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
        
    def midiFormat(self):
        """Returns the MIDI format of this file."""
        return self._format
    
    def setMidiFormat(self, format):
        """Sets the MIDI format of this file."""
        self._format = format
        
    def numTracks(self):
        """Returns the number of tracks of this file."""
        return self._numTracks
    
    def setNumTracks(self, numTracks):
        """Sets the number of tracks of this file."""
        self._numTracks = numTracks
        
    def division(self):
        """Returns the division of this file."""
        return self._division
    
    def setDivision(self, division):
        """Sets the division of this file."""
        self._division = division
        
    def events(self):
        """Returns all the MIDI events in a dictionary.
        
        The events dict's keys are the absolute time.
        The value is a dict containing a list of event objects for every track number.
        
        """
        return self._events
        
    def output(self, output):
        """Write all our events to the output handler (a midi.MidiOutStream instance)."""
        output.header(self._format, self._numTracks, self._division)
        evs = self.events()
        times = sorted(evs)
        for track in range(self._numTracks):
            output.reset_time()
            output.start_of_track(track)
            output.set_current_track(track)
            for time in times:
                try:
                    for ev in evs[time][track]:
                        output.update_time(time, 0)
                        ev.output(output)
                except KeyError:
                    pass
            output.update_time(0)
            output.end_of_track()
        output.eof()

    def save(self, f):
        """Writes ourselves to a MIDI file or file handle."""
        self.output(midi.MidiOutFile.MidiOutFile(f))


