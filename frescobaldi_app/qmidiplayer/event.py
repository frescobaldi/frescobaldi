# This file is part of the qmidiplayer package.
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
    def pm(self):
        """returns the PortMidi message for this event."""
        pass

class NoteEvent(Event):
    """A NoteOn or NoteOff event."""
    def __init__(self, channel, pitch, velocity):
        self.channel = channel
        self.pitch = pitch
        self.velocity = velocity

class NoteOn(NoteEvent):
    def pm(self):
        return [self.channel | 0x90, self.pitch, self.velocity]
        
class NoteOff(NoteEvent):
    def pm(self):
        return [self.channel | 0x80, self.pitch, self.velocity]

