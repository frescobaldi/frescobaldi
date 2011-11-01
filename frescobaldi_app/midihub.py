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

The MIDI support in Frescobaldi is optional (i.e. if PortMidi is not found, the
relevant functions should simply be disabled (with a message that PortMidi is
not available)).

This module uses the portmidi interface that is capable of using PortMIDI in
different ways (via a Python extension module or by embedding the PortMIDI
C library directly).

The available() method returns True if portmidi is available, False if not.

Inside Frescobaldi, interact with this module to get input and outpues etcetera,
not with portmidi directly.

"""

import portmidi

def available():
    """Returns True if portmidi is available, False if not."""
    return portmidi.available()



