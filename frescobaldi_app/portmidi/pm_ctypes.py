# This script embeds the PortMidi Portable MIDI library via ctypes.
# It is based on Grant Yoshida's 2007 version with some updates from
# Christopher Arndt from 2009 with some bugs fixed and restructured a bit.


import os
import sys

from ctypes import (CDLL, CFUNCTYPE, POINTER, Structure, byref, c_char_p,
    c_int32, c_uint, c_void_p, cast, create_string_buffer)

import macosx

# path to portmidi in the standalone .app bundle
_PM_MACOSX_APP = '../Frameworks/libportmidi.dylib'

# the basename of the portmidi/porttime libraries on different platforms
_PM_DLL = dict(
    win32 = 'libportmidi-0',
)
_PT_DLL = dict(
    win32 = 'libporttime-0',
)

if sys.platform.startswith('win'):
    # ctypes.util.find_library() does not implement the full Windows DLL search
    # order, so we have to provide it ourselves, so that the PortMidi DLL can
    # be found. See the docstring of the find_library() function for more
    # information.

    from ctypes import windll, c_wchar_p, create_unicode_buffer

    def get_system_directory():
        """Return the path of the Windos system directory as a unicode string."""
        try:
            windll.kernel32.GetSystemDirectoryW.argtypes = [c_wchar_p, c_uint]
            windll.kernel32.GetSystemDirectoryW.restype = c_uint
        except AttributeError:
            return None
        else:
            path = create_unicode_buffer(256)
            plen = windll.kernel32.GetSystemDirectoryW(path, 256)
            return plen and path.value or None

    def get_windows_directory():
        """Return the path of the Windos directory as a unicode string."""
        try:
            windll.kernel32.GetWindowsDirectoryW.argtypes = [c_wchar_p, c_uint]
            windll.kernel32.GetWindowsDirectoryW.restype = c_uint
        except AttributeError:
            return None
        else:
            path = create_unicode_buffer(256)
            plen = windll.kernel32.GetWindowsDirectoryW(path, 256)
            return plen and path.value or None

    def find_library(name, prepend_paths=None):
        r"""Find and return the path of the given DLL using the DLL search order.

        'name' should be the basename of the DLL with or without the '.dll'
        extension. If 'prepend_paths' is specified, it should be a list of
        directories to be searched before the default ones.

        The default search order searches these directories:

        - The directory from where the application (i.e. the main Python script)
          is loaded
        - The Windows system directory (e.g. C:\Windows\System32)
        - The Windows 16-bit system directory (e.g. C:\Windows\System)
        - The Windows directory (e.g. C:\Windows)
        - The current directory
        - Any directory named on the PATH environment variable

        """
        windir = get_windows_directory()
        search_paths = (prepend_paths or []) + [
            os.path.dirname(sys.argv[0]),
            get_system_directory(),
            os.path.join(windir, 'System'),
            windir,
            os.curdir
        ] + [p for p in os.environ['PATH'].split(os.pathsep) if p]
        for directory in search_paths:
            fname = os.path.join(directory, name)
            if os.path.exists(fname):
                return fname
            if fname.lower().endswith(".dll"):
                continue
            fname = fname + ".dll"
            if os.path.exists(fname):
                return fname
        return None

    dll_name = find_library(_PM_DLL['win32'], [os.path.dirname(__file__)])
elif sys.platform.startswith('darwin') and macosx.inside_app_bundle() and os.path.exists(_PM_MACOSX_APP):
    dll_name = _PM_MACOSX_APP
else:
    from ctypes.util import find_library
    dll_name = find_library(_PM_DLL.get(sys.platform, 'portmidi'))
if dll_name is None:
    raise ImportError("Couldn't find the PortMidi library.")

libpm = CDLL(dll_name)
# The portmidi library may be linked against porttime but not export its
# symbols. Then we need to load the porttime library as well.
if hasattr(libpm, 'Pt_Time'):
    libpt = libpm
else:
    libpt = CDLL(find_library(_PT_DLL.get(sys.platform, 'porttime')))


# portmidi.h

PmError = c_int32
# PmError enum
pmNoError = 0
pmHostError = -10000
pmInvalidDeviceId = -9999
pmInsufficientMemory = -9998
pmBufferTooSmall = -9997
pmBufferOverflow = -9996
pmBadPtr = -9995
pmBadData = -9994
pmInternalError = -9993
pmBufferMaxSize = -9992

libpm.Pm_Initialize.restype = PmError
libpm.Pm_Terminate.restype = PmError

PmDeviceID = c_int32

PortMidiStreamPtr = c_void_p
PmStreamPtr = PortMidiStreamPtr
PortMidiStreamPtrPtr = POINTER(PortMidiStreamPtr)

libpm.Pm_HasHostError.restype = c_int32
libpm.Pm_HasHostError.argtypes = [PortMidiStreamPtr]

libpm.Pm_GetErrorText.restype = c_char_p
libpm.Pm_GetErrorText.argtypes = [PmError]

libpm.Pm_GetHostErrorText.argtypes = [c_char_p, c_uint]

pmNoDevice = -1

class PmDeviceInfo(Structure):
    _fields_ = [("structVersion", c_int32),
                ("interf", c_char_p),
                ("name", c_char_p),
                ("input", c_int32),
                ("output", c_int32),
                ("opened", c_int32)]

PmDeviceInfoPtr = POINTER(PmDeviceInfo)

libpm.Pm_CountDevices.restype = c_int32
libpm.Pm_GetDefaultOutputDeviceID.restype = PmDeviceID
libpm.Pm_GetDefaultInputDeviceID.restype = PmDeviceID

PmTimestamp = c_int32
PmTimeProcPtr = CFUNCTYPE(PmTimestamp, c_void_p)
NullTimeProcPtr = cast(None, PmTimeProcPtr)

# PmBefore is not defined

libpm.Pm_GetDeviceInfo.argtypes = [PmDeviceID]
libpm.Pm_GetDeviceInfo.restype = PmDeviceInfoPtr

libpm.Pm_OpenInput.restype = PmError
libpm.Pm_OpenInput.argtypes = [PortMidiStreamPtrPtr,
                             PmDeviceID,
                             c_void_p,
                             c_int32,
                             PmTimeProcPtr,
                             c_void_p]

libpm.Pm_OpenOutput.restype = PmError
libpm.Pm_OpenOutput.argtypes = [PortMidiStreamPtrPtr,
                             PmDeviceID,
                             c_void_p,
                             c_int32,
                             PmTimeProcPtr,
                             c_void_p,
                             c_int32]

libpm.Pm_SetFilter.restype = PmError
libpm.Pm_SetFilter.argtypes = [PortMidiStreamPtr, c_int32]

libpm.Pm_SetChannelMask.restype = PmError
libpm.Pm_SetChannelMask.argtypes = [PortMidiStreamPtr, c_int32]

libpm.Pm_Abort.restype = PmError
libpm.Pm_Abort.argtypes = [PortMidiStreamPtr]

libpm.Pm_Close.restype = PmError
libpm.Pm_Close.argtypes = [PortMidiStreamPtr]

PmMessage = c_int32

class PmEvent(Structure):
    _fields_ = [("message", PmMessage),
                ("timestamp", PmTimestamp)]

PmEventPtr = POINTER(PmEvent)

libpm.Pm_Read.restype = PmError
libpm.Pm_Read.argtypes = [PortMidiStreamPtr, PmEventPtr, c_int32]

libpm.Pm_Poll.restype = PmError
libpm.Pm_Poll.argtypes = [PortMidiStreamPtr]

libpm.Pm_Write.restype = PmError
libpm.Pm_Write.argtypes = [PortMidiStreamPtr, PmEventPtr, c_int32]

libpm.Pm_WriteShort.restype = PmError
libpm.Pm_WriteShort.argtypes = [PortMidiStreamPtr, PmTimestamp, c_int32]

libpm.Pm_WriteSysEx.restype = PmError
libpm.Pm_WriteSysEx.argtypes = [PortMidiStreamPtr, PmTimestamp, c_char_p]

# porttime.h

# PtError enum
PtError = c_int32
ptNoError = 0
ptHostError = -10000
ptAlreadyStarted = -9999
ptAlreadyStopped = -9998
ptInsufficientMemory = -9997

PtTimestamp = c_int32
PtCallback = CFUNCTYPE(PmTimestamp, c_void_p)

libpt.Pt_Start.restype = PtError
libpt.Pt_Start.argtypes = [c_int32, PtCallback, c_void_p]

libpt.Pt_Stop.restype = PtError
libpt.Pt_Started.restype = c_int32
libpt.Pt_Time.restype = PtTimestamp

