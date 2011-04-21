"""
This module tries to import the binary pypm module from pygame without
importing other parts of pygame.

The module provides an api comparable to the pygame.midi api.

See for documentation the pygame.midi docs.
"""

# import the pygame pypm binding without importing all of pygame

import imp

# raises ImportError when not found
pygame_path = imp.find_module('pygame')[1]
file_handle, path, description = imp.find_module('pypm', [pygame_path])
_pypm = imp.load_module('pypm', file_handle, path, description)
del pygame_path, file_handle, path, description

import atexit

_init = None

def init():
    """initialize the midi module"""
    global _init
    if _init is None:
        atexit.register(quit)
    if not _init:
        _pypm.Initialize()
        _init = True

def quit():
    """uninitialize the midi module"""
    global _init
    if _init:
        _pypm.Terminate()
        _init = False

def _check_init():
    if not _init:
        raise RuntimeError("pygame.midi not initialised.")

def get_count():
    """gets the number of devices."""
    _check_init()
    return _pypm.CountDevices()

def get_default_input_id():
    """gets default input device number"""
    return _pypm.GetDefaultInputDeviceID()

def get_default_output_id():
    """gets default output device number"""
    _check_init()
    return _pypm.GetDefaultOutputDeviceID()

def get_device_info(an_id):
    """ returns information about a midi device"""
    _check_init()
    return _pypm.GetDeviceInfo(an_id) 


class Input(object):
    """Input is used to get midi input from midi devices."""

    def __init__(self, device_id, buffer_size=4096):
        _check_init()
 
        if device_id == -1:
            raise MidiException("Device id is -1, not a valid output id.  -1 usually means there were no default Output devices.")
            
        try:
            r = get_device_info(device_id)
        except TypeError:
            raise TypeError("an integer is required")
        except OverflowError:
            raise OverflowError("long int too large to convert to int")

        # and now some nasty looking error checking, to provide nice error 
        #   messages to the kind, lovely, midi using people of whereever.
        if r:
            interf, name, input, output, opened = r
            if input:
                try:
                    self._input = _pypm.Input(device_id, buffer_size)
                except TypeError:
                    raise TypeError("an integer is required")
                self.device_id = device_id

            elif output:
                raise MidiException("Device id given is not a valid input id, it is an output id.")
            else:
                raise MidiException("Device id given is not a valid input id.")
        else:
            raise MidiException("Device id invalid, out of range.")

    def _check_open(self):
        if self._input is None:
            raise MidiException("midi not open.")

    def close(self):
        """ closes a midi stream, flushing any pending buffers."""
        _check_init()
        if not (self._input is None):
            self._input.Close()
        self._input = None

    def read(self, num_events):
        """reads num_events midi events from the buffer."""
        _check_init()
        self._check_open()
        return self._input.Read(num_events)

    def poll(self):
        """returns true if there's data, or false if not."""
        _check_init()
        self._check_open()

        r = self._input.Poll()
        if r == _pypm.TRUE:
            return True
        elif r == _pypm.FALSE:
            return False
        else:
            err_text = _pypm.GetErrorText(r)
            raise MidiException( (r, err_text) )


class Output(object):
    """Output is used to send midi to an output device"""

    def __init__(self, device_id, latency = 0, buffer_size = 4096):
     
        _check_init()
        self._aborted = 0

        if device_id == -1:
            raise MidiException("Device id is -1, not a valid output id.  -1 usually means there were no default Output devices.")
            
        try:
            r = get_device_info(device_id)
        except TypeError:
            raise TypeError("an integer is required")
        except OverflowError:
            raise OverflowError("long int too large to convert to int")

        # and now some nasty looking error checking, to provide nice error 
        #   messages to the kind, lovely, midi using people of whereever.
        if r:
            interf, name, input, output, opened = r
            if output:
                try:
                    self._output = _pypm.Output(device_id, latency)
                except TypeError:
                    raise TypeError("an integer is required")
                self.device_id = device_id

            elif input:
                raise MidiException("Device id given is not a valid output id, it is an input id.")
            else:
                raise MidiException("Device id given is not a valid output id.")
        else:
            raise MidiException("Device id invalid, out of range.")

    def _check_open(self):
        if self._output is None:
            raise MidiException("midi not open.")

        if self._aborted:
            raise MidiException("midi aborted.")

    def close(self):
        """ closes a midi stream, flushing any pending buffers."""
        _check_init()
        if not (self._output is None):
            self._output.Close()
        self._output = None

    def abort(self):
        """terminates outgoing messages immediately."""
        _check_init()
        if self._output:
            self._output.Abort()
        self._aborted = 1

    def write(self, data):
        """writes a list of midi data to the Output"""
        _check_init()
        self._check_open()
        self._output.Write(data)

    def write_short(self, status, data1 = 0, data2 = 0):
        """output MIDI information of 3 bytes or less."""
        _check_init()
        self._check_open()
        self._output.WriteShort(status, data1, data2)

    def write_sys_ex(self, when, msg):
        """writes a timestamped system-exclusive midi message."""
        _check_init()
        self._check_open()
        self._output.WriteSysEx(when, msg)

    def note_on(self, note, velocity=None, channel = 0):
        """turns a midi note on.  Note must be off."""
        if velocity is None:
            velocity = 0
        if not (0 <= channel <= 15):
            raise ValueError("Channel not between 0 and 15.")
        self.write_short(0x90+channel, note, velocity)

    def note_off(self, note, velocity=None, channel = 0):
        """turns a midi note off.  Note must be on."""
        if velocity is None:
            velocity = 0
        if not (0 <= channel <= 15):
            raise ValueError("Channel not between 0 and 15.")
        self.write_short(0x80 + channel, note, velocity)


    def set_instrument(self, instrument_id, channel = 0):
        """select an instrument, with a value between 0 and 127"""
        if not (0 <= instrument_id <= 127):
            raise ValueError("Undefined instrument id: %d" % instrument_id)
        if not (0 <= channel <= 15):
            raise ValueError("Channel not between 0 and 15.")
        self.write_short(0xc0+channel, instrument_id)


def time():
    """returns the current time in ms of the PortMidi timer"""
    return _pypm.Time()


class MidiException(Exception):
    """exception that pygame.midi functions and classes can raise"""
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

