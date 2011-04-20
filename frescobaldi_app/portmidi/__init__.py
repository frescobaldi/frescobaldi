"""
This packages accesses the low-level, cross-platform PortMidi library via ctypes.
This file defines the (simple) API, loosely based on the PyGame.MIDI api.
"""

from .constants import *
from .pm_ctypes import (
    libpm, libpt,
    pmHostError, PmEvent,
    PmTimeProcPtr, NullTimeProcPtr,
    PortMidiStreamPtr,
)


def init():
    """Initializes the PortMidi library.
    
    Must be called before anything else.
    
    """
    libpm.Pm_Initialize()
    # equiv to TIME_START: start timer w/ ms accuracy
    libpt.Pt_Start(1, NullTimeProcPtr, None)

def quit():
    """De-initializes the PortMidi library.

    Call this to clean up Midi streams when done. If you do not call this on
    Windows machines when you are done with MIDI, your system may crash.

    """
    libpm.Pm_Terminate()

def count():
    """Returns the number of available MIDI devices."""
    return libpm.Pm_CountDevices()

def device_info(device_id):
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

def default_output_device():
    """Return ID of the current default MID output device."""
    return libpm.Pm_GetDefaultOutputDeviceID()

def default_input_device():
    """Return ID of the current default MIDI input device."""
    return libpm.Pm_GetDefaultInputDeviceID()

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

