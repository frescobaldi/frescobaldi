"""
This packages makes the low-level, cross-platform PortMidi library accessible
via ctypes.

This file defines the (simple) API, loosely based on the pygame.midi API.

For many use cases, this package could be used as a fallback is pygame.midi is
not available. E.g.:

try:
    import pygame.midi as pmidi
except ImportError:
    try:
        import portmidi as pmidi
    except ImportError:
        ... no MIDI support available
    

The PortMidi library should be installed separately.
Get it from: http://portmedia.sourceforge.net/

"""

from __future__ import unicode_literals

import array
import atexit

from ctypes import byref, create_string_buffer

from .constants import *
from .pm_ctypes import (
    libpm, libpt,
    pmHostError, PmEvent,
    PmTimeProcPtr, NullTimeProcPtr,
    PortMidiStreamPtr,
)


_initialized = None


def init():
    """Initializes the PortMidi library.
    
    Must be called before anything else.
    
    """
    
    libpm.Pm_Initialize()
    # equiv to TIME_START: start timer w/ ms accuracy
    libpt.Pt_Start(1, NullTimeProcPtr, None)
    
    global _initialized
    if _initialized is None:
        # only the very first time
        atexit.register(quit)
    _initialized = True

def quit():
    """De-initializes the PortMidi library.

    Call this to clean up Midi streams when done. If you do not call this on
    Windows machines when you are done with MIDI, your system may crash.

    """
    libpm.Pm_Terminate()
    
    global _initialized
    if _initialized is True:
        _initialized = False

def get_count():
    """Returns the number of available MIDI devices."""
    return libpm.Pm_CountDevices()

def get_device_info(device_id):
    """Returns 5-item tuple parameters with information about the given device.

    Returns a tuple with the following five elements:

    - underlying MIDI API (str)
    - device name (str)
    - True if input is available (bool)
    - True if output is available (bool)
    - True if device stream is already open (bool)

    """
    info_ptr = libpm.Pm_GetDeviceInfo(device_id)
    if info_ptr:
        info = info_ptr.contents
        return (info.interf, info.name, bool(info.input), bool(info.output),
            bool(info.opened))

def get_default_input_id():
    """Return ID of the current default MIDI input device."""
    return libpm.Pm_GetDefaultInputDeviceID()

def get_default_output_id():
    """Return ID of the current default MID output device."""
    return libpm.Pm_GetDefaultOutputDeviceID()

def time():
    """Returns the current time of the PortMidi timer in milliseconds."""
    return libpt.Pt_Time()

def error_text(err_no):
    """Return human-readable error message for the given error number."""
    return libpm.Pm_GetErrorText(err_no)

def channel(channel_no):
    """Create a channel filter mask to use on MIDI input streams.

    @param channel_no: MIDI channel number (1-16)
    @type: int

    Example: to receive input on channels 1 and 10 on a MIDI stream called
    MidiIn::

        MidiIn.set_channel_mask(pm.channel(1) | pm.channel(10))

    .. note: The channel function has been altered from the original PortMidi C
        function to correct for what seems to be a bug -- i.e. channels were
        all numbered from 0 to 15 instead of 1 to 16.

    """
    return libpm.Pm_Channel(channel_no - 1)

def check_error(err_no):
    """Check if given err_no is < 0 and raise an appropriate exception.

    @param err_no: error number as returned by various PortMidi functions
    @type err_no: int

    """
    if err_no < 0:
        if err_no == pmHostError:
            err_msg = create_string_buffer('\000' * 256)
            libpm.Pm_GetHostErrorText(err_msg, err_no)
            err_msg = err_msg.value
        else:
            err_msg = libpm.Pm_GetErrorText(err_no)
        raise MidiException(err_no, err_msg)


class MidiException(Exception):
    """Raised on PortMidi errors.
    
    The err_no attribute defines the PortMidi error number.
    The err_msg defines the message string for the error.
    
    """
    def __init__(self, err_no, err_msg):
        super(MidiException, self).__init__(err_msg)
        self.err_no = err_no
        self.err_msg = err_msg
    
    def __str__(self):
        return "[{0}] {1}".format(self.err_no, self.err_msg)


class Output(object):
    """Define a MIDI output stream and attach it to a MIDI output device.

    Example::

        out = Output(device_id, latency)

    See the documentation of the ``__init__`` method for more information.

    """

    def __init__(self, device_id, latency=0, bufsize=1024):
        """Object initilisator.

        @param device_id: the ID of the output device to open. The available
            device IDs can be found out with ``get_default_output_device_id()``
            or ``count_devices()``.
        @type device_id: int

        @param latency: the delay in milliseconds applied to timestamps to
            determine when the output should actually occur. (If latency is
            ``< 0``, 0 is assumed.) If latency is zero, timestamps are ignored
            and all output is delivered immediately. If latency is greater than
            zero, output is delayed until the message timestamp plus the
            latency. latency is in milliseconds.
        @type latency: int

        @param bufsize: the default size of the event buffer used for write
            operations (optional). The default value is 1024 events.

        """

        self.device_id = device_id
        self.latency = latency
        self.buffer_size = bufsize
        self._midi_stream = PortMidiStreamPtr()
        self._opened = False
        self._open_device()

    def _open_device(self):
        err = libpm.Pm_OpenOutput(byref(self._midi_stream), self.device_id,
            None, 0, NullTimeProcPtr, None, self.latency)
        check_error(err)
        self._opened = True

    def close(self):
        """Closes a midi stream, flushing any pending buffers."""
        if self._opened and get_device_info(self.device_id)[4]:
            err = libpm.Pm_Abort(self._midi_stream)
            check_error(err)
            err = libpm.Pm_Close(self._midi_stream)
            check_error(err)
            self._opened = False
        
    __del__ = close

    def write(self, data, bufsize=None):
        """Send the given series of data to the output device.

        @param data: a series of MIDI events in the form of a list::

            out.write([((status <, data1><, data2><, data3>), timestamp),
                      [(status<, data1><, data2><, data3>), timestamp),...])

        @type data: list with max. 1024 events

        @param bufsize: size of the output event buffer for this write
            operation (optional). If not specied, the buffer size set at
            instance creation time is used. ``bufsize`` must be
            ``>= len(data)``.
        @type: int

        The number of required ``data`` fields depends on the type of the MIDI
        message determined by the status field. For example (assuming ``out``
        is an ``Output`` instance):

            out.write([((MIDI_PROGRAM, 0, 0), 20000)])

        is equivalent to::

            out.write([((MIDI_PROGRAM), 20000)])

        Examples:

        Send a program change message for program 1 at time 20000 and send a
        note on message for note 65 with velocity 100 500 ms later::

            out.write([
                ((MIDI_PROGRAM, 0, 0), 20000),
                ((MIDI_NOTE_ON, 60,100), 20500)
            ])

        .. note::
            1. Timestamps will be ignored if ``latency = 0``.
            2. To get a note to play immediately, send MIDI info with a
               timestamp read from function ``time()``.

        """
        buffer_size = bufsize or self.buffer_size

        if len(data) > buffer_size:
            raise ValueError(
                "Number of events in data (%s) exceeds buffer size (%i)" %
                (len(data), buffer_size))

        BufferType = PmEvent * buffer_size
        buffer = BufferType()

        for i, event in enumerate(data):
            msg = event[0]
            if len(msg) > 4 or len(msg) < 1:
                raise ValueError(
                    'Too few or many (%i) arguments in event list' % len(msg))
            buffer[i].message = 0
            for j, byte in enumerate(msg):
                buffer[i].message += ((byte & 0xFF) << (8*j))
            buffer[i].timestamp = event[1]
        err = libpm.Pm_Write(self._midi_stream, buffer, len(data))
        check_error(err)

    def write_short(self, status, data1=0, data2=0):
        """Send a MIDI mssage of 3 bytes or less to the output device.

        @param status: the MIDI status byte, for example ``0xc0`` for a program
            change message or ``0x90`` for note on etc. You may use the
            provided module level constants for the status byte.
        @type: int

        @param data1: the first data byte (optional). If omitted, 0 is assumed.
        @type data1: int

        @param data1: the first data byte (optional). If omitted, 0 is assumed.
        @type data1: int

        Example (assuming ``out`` is an ``Output`` instance):

        Send a note on message with note 65 and velocity 100::

            out.write_short(MIDI_NOTE_ON, 65, 100)

        """
        buffer = PmEvent()
        buffer.timestamp = libpt.Pt_Time()
        buffer.message = (((data2 << 16) & 0xFF0000) |
            ((data1 << 8) & 0xFF00) | (status & 0xFF))
        err = libpm.Pm_Write(self._midi_stream, buffer, 1)
        check_error(err)

    def write_sysex(self, when, msg):
        """Send a timestamped system-exclusive MIDI message to the output device.

        @param when: when to send the sysex data
        @type when: an int a

        @param msg: the sysex data as a byte string
        @type msg: list or str

        Examples (assuming ``out`` is an ``Output`` instance):

            out.write_sysex(0, '\\xF0\\x7D\\x10\\x11\\x12\\x13\\xF7')

        is equivalent to::

            out.write_sysex(time(), [0xF0, 0x7D, 0x10, 0x11, 0x12, 0x13, 0xF7])

        """
        if isinstance(msg, (tuple, list)):
            msg = array.array('B', msg).tostring()
        cur_time = time()
        err = libpm.Pm_WriteSysEx(self._midi_stream, when, msg)
        check_error(err)
        while time() == cur_time:
            pass

    def note_on(self, note, velocity=80, channel = 0):
        """turns a midi note on.  Note must be off.
        Output.note_on(note, velocity=80, channel = 0)

        Turn a note on in the output stream.  The note must already
        be off for this to work correctly.
        """
        if not (0 <= channel <= 15):
            raise ValueError("Channel not between 0 and 15.")
        self.write_short(0x90+channel, note, velocity)

    def note_off(self, note, velocity=0, channel = 0):
        """turns a midi note off.  Note must be on.
        Output.note_off(note, velocity=None, channel = 0)

        Turn a note off in the output stream.  The note must already
        be on for this to work correctly.
        """
        if not (0 <= channel <= 15):
            raise ValueError("Channel not between 0 and 15.")
        self.write_short(0x80 + channel, note, velocity)


    def set_instrument(self, instrument_id, channel = 0):
        """select an instrument, with a value between 0 and 127
        Output.set_instrument(instrument_id, channel = 0)

        """
        if not (0 <= instrument_id <= 127):
            raise ValueError("Undefined instrument id: %d" % instrument_id)
        if not (0 <= channel <= 15):
            raise ValueError("Channel not between 0 and 15.")
        self.write_short(0xc0+channel, instrument_id)


class Input(object):
    """Define a MIDI input stream and attach it to a MIDI input device.

    Example::

        input = Input(device_id)

    See the documentation of the ``__init__`` method for more information.

    """

    def __init__(self, device_id, bufsize=1024):
        """Object initilisator.

        @param device_id: the ID of the input device to open. The available
            device IDs can be found out with default_input_device()``
            or ``count()``.
        @type device_id: int

        @param bufsize: the default size of the event buffer used for read
            operations (optional). The default value is 1024 events.

        """
        self.device_id = device_id
        self.buffer_size = bufsize
        self._midi_stream = PortMidiStreamPtr()
        self._opened = False
        self._open_device()

    def _open_device(self):
        err = libpm.Pm_OpenInput(byref(self._midi_stream), self.device_id,
            None, 100, NullTimeProcPtr, None)
        check_error(err)
        self._opened = True

    def close(self):
        """Closes a midi stream, flushing any pending buffers."""
        if self._opened and get_device_info(self.device_id)[4]:
            err = libpm.Pm_Abort(self._midi_stream)
            check_error(err)
            err = libpm.Pm_Close(self._midi_stream)
            check_error(err)
            self._opened = False
        
    __del__ = close

    def set_filter(self, filter):
        """Sets filter on an open input stream to drop selected MIDI messages.

        @param filter: one or several filter types from the FILT_* constants
            OR'ed together to form a bitmask
        @type filter: int

        By default, only active sensing messages are filtered. To prohibit,
        for example, active sensing and sysex messages, call::

           input.set_filter(stream, FILT_ACTIVE | FILT_SYSEX)

        Filtering is useful when midi routing or midi thru functionality is
        being provided by the user application. For example, you may want to
        exclude timing messages (clock, MTC, start/stop/continue), while
        allowing note-related messages to pass. Or you may be using a sequencer
        or drum-machine for MIDI clock information but want to exclude any
        notes it may play.

        .. note:: ``set_filter`` empties the buffer after setting the filter,
            just in case anything got through.

        """
        buffer = PmEvent()

        err = libpm.Pm_SetFilter(self._midi_stream, filters)
        check_error(err)

        while libpm.Pm_Poll(self._midi_stream) != 0:
            err = Pm_Read(self._midi_stream, buffer, 1)
            check_error(err)

    def set_channel_mask(self, mask):
        """Set filter mask for filtering incoming messages based on channel.

        @param mask: The mask is a 16-bit bitfield corresponding to appropriate
            channels.
        @type mask: int

        The module function ``channel(channel_no)`` can assist in calling this
        function. For example, to receive only events on channel 1 with the
        ``Input`` instance ``input``::

            input.set_channel_mask(channel(1))

        Multiple channels should be OR'd together::

            input.set_channel_mask(channel(10) | channel(11))

        ..note:
            The ``channel()`` function has been altered from the original
            PortMidi C function to correct for what seems to be a bug --
            i.e. channels were all numbered from 0 to 15 instead of 1 to 16.

        """
        err = libpm.Pm_SetChannelMask(self._midi_stream, mask)
        check_error(err)

    def poll(self):
        """Polls the input stream to test whether input is available.

        Return True, False, or raise an exception on error.

        """
        assert self._midi_stream 
        err = libpm.Pm_Poll(self._midi_stream)
        check_error(err)
        return bool(err)

    def read(self, length, bufsize=None):
        """Return up to length midi events from the input buffer as a list.

        @param length: number of events to return at maximum
        @type length: int

        @param bufsize: size of the input event buffer for this read operation
            (optional). If not specied, the buffer size set at instance
            creation time is used. ``bufsize`` must be ``>= length``.
        @type: int

        The format of the returned list is the same one as expected for the
        ``data`` argument of the ``Output.write()`` method::

            [
              ((status, data1, data2, data3), timestamp),
              ((status, data1, data2, data3), timestamp),
              ...
            ]

        Example:

            input.read(50)

        Returns all the events in the buffer, up to 50 events.

        """
        buffer_size = bufsize or self.buffer_size
        BufferType = PmEvent * buffer_size
        buffer = BufferType()

        if length > buffer_size:
            raise ValueError("Value %i for length exceeds buffer size (%i)" %
                (length, buffer_size))
        if length < 1:
            raise ValueError('Minimum buffer length is 1')
        num_events = libpm.Pm_Read(self._midi_stream, buffer, length)
        check_error(num_events)

        data = []
        for i in xrange(num_events):
            ev = buffer[i]
            msg = ev.message
            msg = (msg & 255, (msg>>8) & 255, (msg>>16) & 255, (msg>>24) & 255)
            data.append((msg, ev.timestamp))
        return data


