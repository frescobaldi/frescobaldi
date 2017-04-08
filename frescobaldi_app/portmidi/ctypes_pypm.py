# This module provides the same api via ctypes as John Harrison's pyrex-based
# PortMIDI binding.
# Don't use this module directly but via the toplevel API of this package.
# Copyright (c) 2011 - 2014 by Wilbert Berendsen, placed in the public domain.

import array
from ctypes import byref, create_string_buffer

from .pm_ctypes import (
    libpm, libpt,
    pmHostError, PmEvent,
    PmTimeProcPtr, NullTimeProcPtr,
    PortMidiStreamPtr,
)

from . import MidiException


__all__ = [
    'TRUE',
    'FALSE',
    'Initialize',
    'Terminate',
    'CountDevices',
    'GetDeviceInfo',
    'GetDefaultInputDeviceID',
    'GetDefaultOutputDeviceID',
    'GetErrorText',
    'Time',
    'Input',
    'Output',
]


FALSE = 0
TRUE = 1


def Initialize():
    libpm.Pm_Initialize()
    # equiv to TIME_START: start timer w/ ms accuracy
    libpt.Pt_Start(1, NullTimeProcPtr, None)


def Terminate():
    libpm.Pm_Terminate()


def GetDeviceInfo(device_id):
    info_ptr = libpm.Pm_GetDeviceInfo(device_id)
    if info_ptr:
        info = info_ptr.contents
        return (
            info.interf,
            info.name,
            bool(info.input),
            bool(info.output),
            bool(info.opened),
        )


CountDevices = libpm.Pm_CountDevices
GetDefaultInputDeviceID = libpm.Pm_GetDefaultInputDeviceID
GetDefaultOutputDeviceID = libpm.Pm_GetDefaultOutputDeviceID
GetErrorText = libpm.Pm_GetErrorText
Time = libpt.Pt_Time


class Output(object):
    buffer_size = 1024
    def __init__(self, device_id, latency=0):
        self.device_id = device_id
        self.latency = latency
        self._midi_stream = PortMidiStreamPtr()
        self._open = False
        self._open_device()

    def _open_device(self):
        err = libpm.Pm_OpenOutput(byref(self._midi_stream), self.device_id,
            None, 0, NullTimeProcPtr, None, self.latency)
        _check_error(err)
        self._open = True

    def Close(self):
        if self._open and GetDeviceInfo(self.device_id)[4]:
            err = libpm.Pm_Abort(self._midi_stream)
            _check_error(err)
            err = libpm.Pm_Close(self._midi_stream)
            _check_error(err)
            self._open = False

    __del__ = Close

    def Write(self, data):
        bufsize = self.buffer_size

        if len(data) > bufsize:
            raise ValueError("too much data for buffer")

        BufferType = PmEvent * bufsize
        buf = BufferType()

        for i, event in enumerate(data):
            msg, buf[i].timestamp = event
            if len(msg) > 4 or len(msg) < 1:
                raise ValueError("invalid message size")
            message = 0
            for j, byte in enumerate(msg):
                message += ((byte & 0xFF) << (8*j))
            buf[i].message = message
        err = libpm.Pm_Write(self._midi_stream, buf, len(data))
        _check_error(err)

    def WriteShort(self, status, data1=0, data2=0):
        buf = PmEvent()
        buf.timestamp = libpt.Pt_Time()
        buf.message = (((data2 << 16) & 0xFF0000) |
            ((data1 << 8) & 0xFF00) | (status & 0xFF))
        err = libpm.Pm_Write(self._midi_stream, buf, 1)
        _check_error(err)

    def WriteSysEx(self, timestamp, msg):
        """msg may be a tuple or list of ints, or a bytes string."""
        if isinstance(msg, (tuple, list)):
            msg = array.array('B', msg).tostring()
        cur_time = Time()
        err = libpm.Pm_WriteSysEx(self._midi_stream, timestamp, msg)
        _check_error(err)
        while Time() == cur_time:
            pass


class Input(object):
    def __init__(self, device_id, bufsize=1024):
        self.device_id = device_id
        self.buffer_size = bufsize
        self._midi_stream = PortMidiStreamPtr()
        self._open = False
        self._open_device()

    def _open_device(self):
        err = libpm.Pm_OpenInput(byref(self._midi_stream), self.device_id,
            None, 100, NullTimeProcPtr, None)
        _check_error(err)
        self._open = True

    def Close(self):
        """Closes a midi stream, flushing any pending buffers."""
        if self._open and GetDeviceInfo(self.device_id)[4]:
            err = libpm.Pm_Close(self._midi_stream)
            _check_error(err)
            self._open = False

    __del__ = Close

    def Poll(self):
        return libpm.Pm_Poll(self._midi_stream)

    def Read(self, length):
        bufsize = self.buffer_size
        BufferType = PmEvent * bufsize
        buf = BufferType()

        if not 1 <= length <= bufsize:
            raise ValueError("invalid length")
        num_events = libpm.Pm_Read(self._midi_stream, buf, length)
        _check_error(num_events)

        data = []
        for i in range(num_events):
            ev = buf[i]
            msg = ev.message
            msg = (msg & 255, (msg>>8) & 255, (msg>>16) & 255, (msg>>24) & 255)
            data.append((msg, ev.timestamp))
        return data


def _check_error(err_no):
    if err_no < 0:
        if err_no == pmHostError:
            err_msg = create_string_buffer(b'\000' * 256)
            libpm.Pm_GetHostErrorText(err_msg, 256)
            err_msg = err_msg.value
        else:
            err_msg = libpm.Pm_GetErrorText(err_no)
        raise MidiException(
            "PortMIDI-ctypes error [{0}]: {1}".format(err_no,
                                                      err_msg.decode('utf-8')))


