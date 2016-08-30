# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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

Inside Frescobaldi, interact with this module to get input and outputs etcetera,
not with portmidi directly.

"""



import portmidi
import signals


portmidi.init()


aboutToRestart = signals.Signal()       # emitted before re-init PortMIDI
settingsChanged = signals.Signal()      # emitted when ports are changed, etc


def available():
    """Returns True if portmidi is available, False if not."""
    return portmidi.available()

def restart():
    """Restarts PortMIDI."""
    aboutToRestart()
    portmidi.quit()
    portmidi.init()
    settingsChanged()
    
def refresh_ports():
    """Refreshes the port list."""
    restart()

def get_count():
    """Returns the number of available PortMIDI ports, or 0 if no PortMIDI."""
    return portmidi.get_count() if available() else 0

def device_infos():
    """Yields the device info for all PortMIDI devices."""
    for n in range(get_count()):
        yield portmidi.get_device_info(n)

def output_ports():
    """Returns a list of all the output port names."""
    names = []
    if available():
        for i in device_infos():
            if i.isoutput:
                name = _decode_name(i.name)
                names.append(name)
    return names

def input_ports():
    """Returns a list of all the input port names."""
    names = []
    if available():
        for i in device_infos():
            if i.isinput:
                name = _decode_name(i.name)
                names.append(name)
    return names

def default_output():
    """Returns a probably suitable default MIDI output port name."""
    names = []
    if available():
        for i in device_infos():
            if i.isoutput:
                name = _decode_name(i.name)
                names.append(name)
                if 'through' not in name.lower():
                    return name
    return names[0] if names else ""

def default_input():
    """Returns a probably suitable default MIDI output port name."""
    names = []
    if available():
        for i in device_infos():
            if i.isinput:
                name = _decode_name(i.name)
                names.append(name)
                if 'through' not in name.lower():
                    return name
    return names[0] if names else ""

def output_by_name(name):
    """Returns a portmidi.Output instance for name."""
    for n in range(get_count()):
        i = portmidi.get_device_info(n)
        output_name = _decode_name(i.name)
        if i.isoutput and output_name.startswith(name) and not i.isopen:
            return portmidi.Output(n)

def input_by_name(name):
    """Returns a portmidi.Input instance for name."""
    for n in range(get_count()):
        i = portmidi.get_device_info(n)
        input_name = _decode_name(i.name)
        if i.isinput and input_name.startswith(name) and not i.isopen:
            return portmidi.Input(n)

def _decode_name(s):
    """Helper to decode a device name or interf if it is a bytes type."""
    return s.decode('latin1') if isinstance(s, type(b'')) else s


# allow the MIDI player to run on python time if portmidi is not available:
if available():
    time = portmidi.time
else:
    from time import time as time_
    def time():
        """Returns a time value in msec."""
        return int(time_() * 1000)


