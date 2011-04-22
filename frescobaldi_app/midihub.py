# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Place where MIDI is handled, output, input, signals, etc.

This module tries to import PortMidi with the "new" api like pygame.midi.
First pyportmidi.midi is tried. Then the pypm module of pygame is searched and
if that fails, the portmidi c library is used (if available) via ctypes.

The MIDI support in Frescobaldi is optional (i.e. if PortMidi is not found, the
relevant functions should simply be disabled (with a message that PortMidi is
not available)).

The available() method returns True if portmidi is available, False if not.

If available, the portmidi module api is in the pmidi global of this module.

"""

pmidi = None
for module in (
    'pyportmidi.midi',
    'portmidi_pygame',
    'portmidi_ctypes',
    ):
    try:
        pmidi = __import__(module)
        break
    except ImportError:
        pass



def available():
    """Returns True if portmidi is available, False if not."""
    return pmidi is not None

