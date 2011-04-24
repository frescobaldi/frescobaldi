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

class Event(object):
    """The base type for all MIDI events."""
    def output(self, out):
        """Should write our event to the output event handler."""
        pass

class NoteEvent(Event):
    """A NoteOn or NoteOff event."""
    def __init__(self, channel, pitch, velocity):
        self.channel = channel
        self.pitch = pitch
        self.velocity = velocity

class NoteOn(NoteEvent):
    def output(self, out):
        return out.note_on(self.channel, self.pitch, self.velocity)
        
class NoteOff(NoteEvent):
    def output(self, out):
        return out.note_off(self.channel, self.pitch, self.velocity)

