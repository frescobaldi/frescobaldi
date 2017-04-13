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
midifile.event -- simple Event namedtuple types and a default parsing handler.
"""


import collections


MetaEvent = collections.namedtuple('MetaEvent', 'type data')
SysExEvent = collections.namedtuple('SysExEvent', 'type data')
NoteEvent = collections.namedtuple('NoteEvent', 'type channel note value')
ControllerEvent = collections.namedtuple('ControllerEvent', 'channel number value')
ProgramChangeEvent = collections.namedtuple('ProgramChangeEvent', 'channel number')
ChannelAfterTouchEvent = collections.namedtuple('ChannelAfterTouchEvent', 'channel value')
PitchBendEvent = collections.namedtuple('PitchBendEvent', 'channel value')


class EventFactory(object):
    """Factory for parsed MIDI events.

    The default 'methods' create namedtuple objects.
    You can override one or more of those names to return other objects.

    """
    note_event = NoteEvent
    controller_event = ControllerEvent
    programchange_event = ProgramChangeEvent
    channelaftertouch_event = ChannelAfterTouchEvent
    pitchbend_event = PitchBendEvent
    sysex_event = SysExEvent
    meta_event = MetaEvent


# MIDI message constants
MIDI_CTL_MSB_MAIN_VOLUME = 0x07
MIDI_CTL_ALL_SOUNDS_OFF = 0x78
MIDI_CTL_RESET_CONTROLLERS = 0x79
MIDI_CTL_ALL_NOTES_OFF  = 0x7B

