"""
This package brings the most important parts of the functionality of the
PortMIDI library in a flexible way to Python.

This module provides a simple API to control the most important parts of
PortMIDI, very much like the pygame.midi api.

It needs the PortMIDI library to be installed, and it is also recommended to
install the 'pypm' or 'pyportmidi' module providing a low-level access to the
PortMIDI library. This is a PyRex-based interface by John Harrison, which is
in some Linux distributions part of a package named 'python-portmidi' or
'python-pypm', and also part of the official PortMIDI package, but quite often
not installed by default.

The PyGame package as of version 1.9.1 also installs the 'pypm' module.

This module tries different ways to find the Python binding module. If that
fails, the PortMIDI library itself is loaded (if found) via ctypes.

To affect the order in which the _setup() function tries to import PortMIDI,
the global try_order list can be changed. The first name in the list is tried
first. This only works before init() is called for the first time.

This module can always be imported, but only init() and available() can be used
if PortMIDI itself is not available.

This module itself is in the public domain, and written by Wilbert Berendsen
in fall 2011.


Usage:

import portmidi

# test if portmidi really loaded:
if portmidi.available():
    ... enable MIDI stuff

# start using PortMIDI: init and quit may be used multiple times
portmidi.init()


# list devices:
for i in range(portmidi.get_count()):
    print(i, portmidi.get_device_info(i))


# play notes to device number 2:
o = portmidi.Output(2, 50)
o.note_on(60)
o.note_off(60)


# play a scale:
time = 0
scale = []
for note in 60, 62, 64, 65, 67, 69, 71, 72:
    scale.append([[0x90, note, 80], time])
    scale.append([[0x80, note], time + 400])
    time += 500

o.write([[msg, portmidi.time() + time] for msg, time in scale])

Note that you always have to specify the time when a note is to be played.

"""

import atexit
import collections


__all__ = [
    'available', 'init', 'quit',
    'get_count', 'get_device_info',
    'get_default_input_id', 'get_default_output_id',
    'time',
    'Input', 'Output',
]

pypm = None
_initialized = None



# you can change this before calling init() for the first time
try_order = ['pypm', 'pyportmidi', 'pygame', 'ctypes']


def available():
    """Returns True if PortMIDI is available."""
    return _setup()

def init():
    """Initializes the PortMIDI library for use.

    It is safe to call this more than once.

    """
    global _initialized
    if _setup() and not _initialized:
        pypm.Initialize()
        _initialized = True

def quit():
    """Terminates the PortMIDI library.

    It is safe to call this more than once.
    On application exit this is also called.

    """
    global _initialized
    if pypm and _initialized:
        pypm.Terminate()
        _initialized = False

def get_count():
    """Returns the number if available MIDI devices."""
    _check_initialized()
    return pypm.CountDevices()

def get_default_input_id():
    """Returns the default input device number."""
    _check_initialized()
    return pypm.GetDefaultInputDeviceID()

def get_default_output_id():
    """Returns the default output device number."""
    _check_initialized()
    return pypm.GetDefaultOutputDeviceID()

def get_device_info(device_id):
    """Returns information about a midi device.

    A five-tuple is returned:
    (interf, name, isinput, isoutput, isopen).

    """
    _check_initialized()
    return device_info(*pypm.GetDeviceInfo(device_id))

def time():
    """Returns the current time in ms of the PortMIDI timer."""
    return pypm.Time()


class Input(object):
    """Reads MIDI input from a device."""
    def __init__(self, device_id, buffer_size=4096):
        self._input = None
        _check_initialized()
        _check_device_id(device_id)
        info = get_device_info(device_id)
        if not info.isinput:
            raise MidiException("not an input device")

        self._input = pypm.Input(device_id, buffer_size)

    def close(self):
        """Closes the input stream."""
        if self._input:
            self._input.Close()
        self._input = None

    def read(self, num_events):
        """reads num_events midi events from the buffer."""
        return self._input.Read(num_events)

    def poll(self):
        """Returns True if there's data, otherwise False."""
        r = self._input.Poll()
        if r == pypm.TRUE:
            return True
        elif r == pypm.FALSE:
            return False
        else:
            raise MidiException(pypm.GetErrorText(r).decode('utf-8'))


class Output(object):
    """Writes MIDI output to a device."""
    def __init__(self, device_id, latency = 0, buffer_size = 4096):
        self._output = None
        _check_initialized()
        _check_device_id(device_id)
        info = get_device_info(device_id)
        if not info.isoutput:
            raise MidiException("not an output device")

        self._output = pypm.Output(device_id, latency)

    def close(self):
        """Closes the output stream."""
        if self._output:
            self._output.Close()
        self._output = None

    def write(self, data):
        """Writes a list of MIDI data to the output.

        Each element of the list should be a list[message, timestamp].
        Each message is again a list: [status, data, data, ...]

        """
        self._output.Write(data)

    def write_short(self, status, data1 = 0, data2 = 0):
        """Output MIDI information of 3 bytes or less."""
        self._output.WriteShort(status, data1, data2)

    def write_sys_ex(self, timestamp, message):
        """Writes a timestamped System-Exclusive MIDI message.

        The message may be a list of integers or a bytes string.

        """
        self._output.WriteSysEx(timestamp, message)

    def note_on(self, note, velocity=80, channel = 0):
        """Turns a midi note on."""
        _check_channel(channel)
        self.write_short(0x90 + channel, note, velocity)

    def note_off(self, note, velocity=0, channel = 0):
        """Turns a midi note off."""
        _check_channel(channel)
        self.write_short(0x80 + channel, note, velocity)

    def set_instrument(self, instrument_id, channel = 0):
        """Select an instrument."""
        if not 0 <= instrument_id <= 127:
            raise ValueError("invalid instrument id")
        _check_channel(channel)
        self.write_short(0xC0 + channel, instrument_id)


class MidiException(Exception):
    """Raised on MIDI-specific errors."""
    pass



# helper functions

device_info = collections.namedtuple('device_info',
    'interf name isinput isoutput isopen')

def _check_device_id(device_id):
    if not 0 <= device_id < get_count():
        raise ValueError("invalid device id")

def _check_channel(channel):
    if not 0 <= channel <= 15:
        raise ValueError("invalid channel number (must be 0..15)")

def _check_initialized():
    if not _initialized:
        raise RuntimeError("PortMIDI not initialized.")

def _setup():
    """Tries to import PortMIDI in the order given in the try_order global.

    Only one time the import is tried.
    Returns True if PortMIDI could be loaded.

    """
    global pypm
    if pypm is None:
        for name in try_order:
            try:
                pypm = globals()['_do_import_' + name]()
                break
            except ImportError:
                continue
        else:
            pypm = False
    return bool(pypm)

def _load_module(name):
    """Loads and returns a single module.

    The name may be dotted, but no parent modules are imported.
    Raises ImportError when the module can't be found.

    """
    import imp
    path = None
    for n in name.split('.'):
        file_handle, path, desc = imp.find_module(n, path and [path])
    return imp.load_module(n, file_handle, path, desc)


# these functions try to import PortMIDI, returning the module
def _do_import_pypm():
    """Tries to import pypm (the c binding module) directly.

    Newer Ubuntu releases provide a python-pypm package with this module.

    """
    import pypm
    # Reject incompatible API, such as ActiveState PyPM
    if not hasattr(pypm, "CountDevices"):
        del pypm
        raise ImportError("Unsupported pypm API")
    return pypm

def _do_import_pyportmidi():
    """This tries to import the c Python module from the PortMIDI distribution.

    Unfortunately not many Linux distros also install the Python binding.

    """
    return _load_module('pyportmidi._pyportmidi')

def _do_import_pygame():
    """This tries to import the pypm module from the pygame package."""
    # We don't use 'from pygame import pypm' as that also imports a large
    # part of pygame which we probably don't use.
    return _load_module('pygame.pypm')

def _do_import_ctypes():
    """This tries to load PortMIDI via ctypes."""
    from . import ctypes_pypm
    return ctypes_pypm


