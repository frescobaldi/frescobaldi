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
A MidiObject represents a MIDI file in memory.
"""

import midi.MidiInFile

from . import midiobject
from . import event
from . import loader

MidiObject = midiobject.MidiObject



def load(f):
    """Loads a MIDI file from the given filename or filehandle.
    
    Returns a MidiObject.
    
    """
    m = MidiObject()
    inp = midi.MidiInFile.MidiInFile(loader.Loader(m), f)
    inp.read()
    return m


