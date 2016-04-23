# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
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
The MIDI player for Frescobaldi.
"""


from midifile.event import ControllerEvent, ProgramChangeEvent
import qmidi.player
import midihub


def event_filter(midi_event):
    """If this function returns True, the MIDI event is sent while seeking."""
    return isinstance(midi_event, (ControllerEvent, ProgramChangeEvent))


class Player(qmidi.player.Player):
    """This Player uses the time from midihub."""
    def timer_midi_time(self):
        return midihub.time()

    def position_event(self, old, new):
        """Called when seeking. Performs program changes."""
        super(Player, self).position_event(old, new)
        output = self.output()
        if not output:
            return
        if new > old:
            evs = self._events[old:new]
        else:
            evs = self._events[:new]
            output.reset()
        for time, e in evs:
            if e.midi:
                if isinstance(e.midi, dict):
                    # dict mapping track to events?
                    midi = sum(map(e.midi.get, sorted(e.midi)), [])
                else:
                    midi = e.midi
                # no note events of course
                midi = [mev for mev in midi if event_filter(mev)]
                if midi:
                    output.send_events(midi)


