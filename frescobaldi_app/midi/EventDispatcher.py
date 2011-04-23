# -*- coding: ISO-8859-1 -*-

# std library
from struct import unpack

# custom
from DataTypeConverters import readBew, readVar, varLen, toBytes

# uhh I don't really like this, but there are so many constants to 
# import otherwise
from constants import *


class EventDispatcher:


    def __init__(self, outstream):
        
        """
        
        The event dispatcher generates events on the outstream.
        
        """
        
        # internal values, don't mess with 'em directly
        self.outstream = outstream
        
        # public flags

        # A note_on with a velocity of 0x00 is actually the same as a 
        # note_off with a velocity of 0x40. When 
        # "convert_zero_velocity" is set, the zero velocity note_on's 
        # automatically gets converted into note_off's. This is a less 
        # suprising behaviour for those that are not into the intimate 
        # details of the midi spec.
        self.convert_zero_velocity = 1
        
        # If dispatch_continuos_controllers is true, continuos 
        # controllers gets dispatched to their defined handlers. Else 
        # they just trigger the "continuous_controller" event handler.
        self.dispatch_continuos_controllers = 1 # NOT IMPLEMENTED YET
        
        # If dispatch_meta_events is true, meta events get's dispatched 
        # to their defined events. Else they all they trigger the 
        # "meta_event" handler.
        self.dispatch_meta_events = 1



    def header(self, format, nTracks, division):
        "Triggers the header event"
        self.outstream.header(format, nTracks, division)


    def start_of_track(self, current_track):
        "Triggers the start of track event"
        
        # I do this twice so that users can overwrite the 
        # start_of_track event handler without worrying whether the 
        # track number is updated correctly.
        self.outstream.set_current_track(current_track)
        self.outstream.start_of_track(current_track)
        
    
    def sysex_event(self, data):
        "Dispatcher for sysex events"
        self.outstream.sysex_event(data)
    
    
    def eof(self):
        "End of file!"
        self.outstream.eof()


    def update_time(self, new_time=0, relative=1):
        "Updates relative/absolute time."
        self.outstream.update_time(new_time, relative)
        
        
    def reset_time(self):
        "Updates relative/absolute time."
        self.outstream.reset_time()
        
        
    # Event dispatchers for similar types of events
    
    
    def channel_messages(self, hi_nible, channel, data):
    
        "Dispatches channel messages"
        
        stream = self.outstream
        data = toBytes(data)
        
        if (NOTE_ON & 0xF0) == hi_nible:
            note, velocity = data
            # note_on with velocity 0x00 are same as note 
            # off with velocity 0x40 according to spec!
            if velocity==0 and self.convert_zero_velocity:
                stream.note_off(channel, note, 0x40)
            else:
                stream.note_on(channel, note, velocity)
        
        elif (NOTE_OFF & 0xF0) == hi_nible:
            note, velocity = data
            stream.note_off(channel, note, velocity)
        
        elif (AFTERTOUCH & 0xF0) == hi_nible:
            note, velocity = data
            stream.aftertouch(channel, note, velocity)
        
        elif (CONTINUOUS_CONTROLLER & 0xF0) == hi_nible:
            controller, value = data
            # A lot of the cc's are defined, so we trigger those directly
            if self.dispatch_continuos_controllers:
                self.continuous_controllers(channel, controller, value)
            else:
                stream.continuous_controller(channel, controller, value)
            
        elif (PATCH_CHANGE & 0xF0) == hi_nible:
            program = data[0]
            stream.patch_change(channel, program)
            
        elif (CHANNEL_PRESSURE & 0xF0) == hi_nible:
            pressure = data[0]
            stream.channel_pressure(channel, pressure)
            
        elif (PITCH_BEND & 0xF0) == hi_nible:
            hibyte, lobyte = data
            value = (hibyte<<7) + lobyte
            stream.pitch_bend(channel, value)

        else:

            raise ValueError, 'Illegal channel message!'



    def continuous_controllers(self, channel, controller, value):
    
        "Dispatches channel messages"

        stream = self.outstream
        
        # I am not really shure if I ought to dispatch continuous controllers
        # There's so many of them that it can clutter up the OutStream 
        # classes.
        
        # So I just trigger the default event handler
        stream.continuous_controller(channel, controller, value)



    def system_commons(self, common_type, common_data):
    
        "Dispatches system common messages"
        
        stream = self.outstream
        
        # MTC Midi time code Quarter value
        if common_type == MTC:
            data = readBew(common_data)
            msg_type = (data & 0x07) >> 4
            values = (data & 0x0F)
            stream.midi_time_code(msg_type, values)
        
        elif common_type == SONG_POSITION_POINTER:
            hibyte, lobyte = toBytes(common_data)
            value = (hibyte<<7) + lobyte
            stream.song_position_pointer(value)

        elif common_type == SONG_SELECT:
            data = readBew(common_data)
            stream.song_select(data)

        elif common_type == TUNING_REQUEST:
            # no data then
            stream.tuning_request(time=None)



    def meta_event(self, meta_type, data):
        
        "Dispatches meta events"
        
        stream = self.outstream
        
        # SEQUENCE_NUMBER = 0x00 (00 02 ss ss (seq-number))
        if meta_type == SEQUENCE_NUMBER:
            number = readBew(data)
            stream.sequence_number(number)
        
        # TEXT = 0x01 (01 len text...)
        elif meta_type == TEXT:
            stream.text(data)
        
        # COPYRIGHT = 0x02 (02 len text...)
        elif meta_type == COPYRIGHT:
            stream.copyright(data)
        
        # SEQUENCE_NAME = 0x03 (03 len text...)
        elif meta_type == SEQUENCE_NAME:
            stream.sequence_name(data)
        
        # INSTRUMENT_NAME = 0x04 (04 len text...)
        elif meta_type == INSTRUMENT_NAME:
            stream.instrument_name(data)
        
        # LYRIC = 0x05 (05 len text...)
        elif meta_type == LYRIC:
            stream.lyric(data)
        
        # MARKER = 0x06 (06 len text...)
        elif meta_type == MARKER:
            stream.marker(data)
        
        # CUEPOINT = 0x07 (07 len text...)
        elif meta_type == CUEPOINT:
            stream.cuepoint(data)
        
        # PROGRAM_NAME = 0x08 (05 len text...)
        elif meta_type == PROGRAM_NAME:
            stream.program_name(data)
        
        # DEVICE_NAME = 0x09 (09 len text...)
        elif meta_type == DEVICE_NAME:
            stream.device_name(data)
        
        # MIDI_CH_PREFIX = 0x20 (20 01 channel)
        elif meta_type == MIDI_CH_PREFIX:
            channel = readBew(data)
            stream.midi_ch_prefix(channel)
        
        # MIDI_PORT  = 0x21 (21 01 port (legacy stuff))
        elif meta_type == MIDI_PORT:
            port = readBew(data)
            stream.midi_port(port)
        
        # END_OFF_TRACK = 0x2F (2F 00)
        elif meta_type == END_OF_TRACK:
            stream.end_of_track()
        
        # TEMPO = 0x51 (51 03 tt tt tt (tempo in us/quarternote))
        elif meta_type == TEMPO:
            b1, b2, b3 = toBytes(data)
            # uses 3 bytes to represent time between quarter 
            # notes in microseconds
            stream.tempo((b1<<16) + (b2<<8) + b3)
        
        # SMTP_OFFSET = 0x54 (54 05 hh mm ss ff xx)
        elif meta_type == SMTP_OFFSET:
            hour, minute, second, frame, framePart = toBytes(data)
            stream.smtp_offset(
                    hour, minute, second, frame, framePart)
        
        # TIME_SIGNATURE = 0x58 (58 04 nn dd cc bb)
        elif meta_type == TIME_SIGNATURE:
            nn, dd, cc, bb = toBytes(data)
            stream.time_signature(nn, dd, cc, bb)
        
        # KEY_SIGNATURE = 0x59 (59 02 sf mi)
        elif meta_type == KEY_SIGNATURE:
            sf, mi = toBytes(data)
            stream.key_signature(sf, mi)
        
        # SPECIFIC = 0x7F (Sequencer specific event)
        elif meta_type == SPECIFIC:
            meta_data = toBytes(data)
            stream.sequencer_specific(meta_data)
        
        # Handles any undefined meta events
        else: # undefined meta type
            meta_data = toBytes(data)
            stream.meta_event(meta_type, meta_data)





if __name__ == '__main__':


    from MidiToText import MidiToText
    
    outstream = MidiToText()
    dispatcher = EventDispatcher(outstream)
    dispatcher.channel_messages(NOTE_ON, 0x00, '\x40\x40')