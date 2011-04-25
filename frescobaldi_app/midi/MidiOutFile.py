# -*- coding: ISO-8859-1 -*-

from MidiOutStream import MidiOutStream
from RawOutstreamFile import RawOutstreamFile

from constants import *
from DataTypeConverters import fromBytes, writeVar

class MidiOutFile(MidiOutStream):


    """
    MidiOutFile is an eventhandler that subclasses MidiOutStream.
    """


    def __init__(self, raw_out=''):

        self.raw_out = RawOutstreamFile(raw_out)
        MidiOutStream.__init__(self)
        
    
    def write(self):
        self.raw_out.write()


    def event_slice(self, slc):
        """
        Writes the slice of an event to the current track. Correctly 
        inserting a varlen timestamp too.
        """
        trk = self._current_track_buffer
        trk.writeVarLen(self.rel_time())
        trk.writeSlice(slc)
        
    
    #####################
    ## Midi events


    def note_on(self, channel=0, note=0x40, velocity=0x40):

        """
        channel: 0-15
        note, velocity: 0-127
        """
        slc = fromBytes([NOTE_ON + channel, note, velocity])
        self.event_slice(slc)


    def note_off(self, channel=0, note=0x40, velocity=0x40):

        """
        channel: 0-15
        note, velocity: 0-127
        """
        slc = fromBytes([NOTE_OFF + channel, note, velocity])
        self.event_slice(slc)


    def aftertouch(self, channel=0, note=0x40, velocity=0x40):

        """
        channel: 0-15
        note, velocity: 0-127
        """
        slc = fromBytes([AFTERTOUCH + channel, note, velocity])
        self.event_slice(slc)


    def continuous_controller(self, channel, controller, value):

        """
        channel: 0-15
        controller, value: 0-127
        """
        slc = fromBytes([CONTINUOUS_CONTROLLER + channel, controller, value])
        self.event_slice(slc)
        # These should probably be implemented
        # http://users.argonet.co.uk/users/lenny/midi/tech/spec.html#ctrlnums


    def patch_change(self, channel, patch):

        """
        channel: 0-15
        patch: 0-127
        """
        slc = fromBytes([PATCH_CHANGE + channel, patch])
        self.event_slice(slc)


    def channel_pressure(self, channel, pressure):

        """
        channel: 0-15
        pressure: 0-127
        """
        slc = fromBytes([CHANNEL_PRESSURE + channel, pressure])
        self.event_slice(slc)


    def pitch_bend(self, channel, value):

        """
        channel: 0-15
        value: 0-16383
        """
        msb = (value>>7) & 0xFF
        lsb = value & 0xFF
        slc = fromBytes([PITCH_BEND + channel, msb, lsb])
        self.event_slice(slc)




    #####################
    ## System Exclusive

#    def sysex_slice(sysex_type, data):
#        ""
#        sysex_len = writeVar(len(data)+1)
#        self.event_slice(SYSTEM_EXCLUSIVE + sysex_len + data + END_OFF_EXCLUSIVE)
#
    def system_exclusive(self, data):

        """
        data: list of values in range(128)
        """
        sysex_len = writeVar(len(data)+1)
        self.event_slice(chr(SYSTEM_EXCLUSIVE) + sysex_len + data + chr(END_OFF_EXCLUSIVE))


    #####################
    ## Common events

    def midi_time_code(self, msg_type, values):
        """
        msg_type: 0-7
        values: 0-15
        """
        value = (msg_type<<4) + values
        self.event_slice(fromBytes([MIDI_TIME_CODE, value]))


    def song_position_pointer(self, value):

        """
        value: 0-16383
        """
        lsb = (value & 0x7F)
        msb = (value >> 7) & 0x7F
        self.event_slice(fromBytes([SONG_POSITION_POINTER, lsb, msb]))


    def song_select(self, songNumber):

        """
        songNumber: 0-127
        """
        self.event_slice(fromBytes([SONG_SELECT, songNumber]))


    def tuning_request(self):

        """
        No values passed
        """
        self.event_slice(chr(TUNING_REQUEST))

            
    #########################
    # header does not really belong here. But anyhoo!!!
    
    def header(self, format=0, nTracks=1, division=96):

        """
        format: type of midi file in [0,1,2]
        nTracks: number of tracks. 1 track for type 0 file
        division: timing division ie. 96 ppq.
        
        """        
        raw = self.raw_out
        raw.writeSlice('MThd')
        bew = raw.writeBew
        bew(6, 4) # header size
        bew(format, 2)
        bew(nTracks, 2)
        bew(division, 2)


    def eof(self):

        """
        End of file. No more events to be processed.
        """
        # just write the file then.
        self.write()


    #####################
    ## meta events


    def meta_slice(self, meta_type, data_slice):
        "Writes a meta event"
        slc = fromBytes([META_EVENT, meta_type]) + \
                         writeVar(len(data_slice)) +  data_slice
        self.event_slice(slc)


    def meta_event(self, meta_type, data):
        """
        Handles any undefined meta events
        """
        self.meta_slice(meta_type, fromBytes(data))


    def start_of_track(self, n_track=0):
        """
        n_track: number of track
        """
        self._current_track_buffer = RawOutstreamFile()
        self.reset_time()
        self._current_track = n_track


    def end_of_track(self):
        """
        Writes the track to the buffer.
        """
        raw = self.raw_out
        raw.writeSlice(TRACK_HEADER)
        track_data = self._current_track_buffer.getvalue()
        # wee need to know size of track data.
        eot_slice = writeVar(self.rel_time()) + fromBytes([META_EVENT, END_OF_TRACK, 0])
        raw.writeBew(len(track_data)+len(eot_slice), 4)
        # then write
        raw.writeSlice(track_data)
        raw.writeSlice(eot_slice)
        


    def sequence_number(self, value):

        """
        value: 0-65535
        """
        self.meta_slice(meta_type, writeBew(value, 2))


    def text(self, text):
        """
        Text event
        text: string
        """
        self.meta_slice(TEXT, text)


    def copyright(self, text):

        """
        Copyright notice
        text: string
        """
        self.meta_slice(COPYRIGHT, text)


    def sequence_name(self, text):
        """
        Sequence/track name
        text: string
        """
        self.meta_slice(SEQUENCE_NAME, text)


    def instrument_name(self, text):

        """
        text: string
        """
        self.meta_slice(INSTRUMENT_NAME, text)


    def lyric(self, text):

        """
        text: string
        """
        self.meta_slice(LYRIC, text)


    def marker(self, text):

        """
        text: string
        """
        self.meta_slice(MARKER, text)


    def cuepoint(self, text):

        """
        text: string
        """
        self.meta_slice(CUEPOINT, text)


    def midi_ch_prefix(self, channel):

        """
        channel: midi channel for subsequent data
        (deprecated in the spec)
        """
        self.meta_slice(MIDI_CH_PREFIX, chr(channel))


    def midi_port(self, value):

        """
        value: Midi port (deprecated in the spec)
        """
        self.meta_slice(MIDI_CH_PREFIX, chr(value))


    def tempo(self, value):

        """
        value: 0-2097151
        tempo in us/quarternote
        (to calculate value from bpm: int(60,000,000.00 / BPM))
        """
        hb, mb, lb = (value>>16 & 0xff), (value>>8 & 0xff), (value & 0xff)
        self.meta_slice(TEMPO, fromBytes([hb, mb, lb]))


    def smpt_offset(self, hour, minute, second, frame, framePart):

        """
        hour,
        minute,
        second: 3 bytes specifying the hour (0-23), minutes (0-59) and 
                seconds (0-59), respectively. The hour should be 
                encoded with the SMPTE format, just as it is in MIDI 
                Time Code.
        frame: A byte specifying the number of frames per second (one 
               of : 24, 25, 29, 30).
        framePart: A byte specifying the number of fractional frames, 
                   in 100ths of a frame (even in SMPTE-based tracks 
                   using a different frame subdivision, defined in the 
                   MThd chunk).
        """
        self.meta_slice(SMTP_OFFSET, fromBytes([hour, minute, second, frame, framePart]))



    def time_signature(self, nn, dd, cc, bb):

        """
        nn: Numerator of the signature as notated on sheet music
        dd: Denominator of the signature as notated on sheet music
            The denominator is a negative power of 2: 2 = quarter 
            note, 3 = eighth, etc.
        cc: The number of MIDI clocks in a metronome click
        bb: The number of notated 32nd notes in a MIDI quarter note 
            (24 MIDI clocks)        
        """
        self.meta_slice(TIME_SIGNATURE, fromBytes([nn, dd, cc, bb]))




    def key_signature(self, sf, mi):

        """
        sf: is a byte specifying the number of flats (-ve) or sharps 
            (+ve) that identifies the key signature (-7 = 7 flats, -1 
            = 1 flat, 0 = key of C, 1 = 1 sharp, etc).
        mi: is a byte specifying a major (0) or minor (1) key.
        """
        self.meta_slice(KEY_SIGNATURE, fromBytes([sf, mi]))



    def sequencer_specific(self, data):

        """
        data: The data as byte values
        """
        self.meta_slice(SEQUENCER_SPECIFIC, data)





#    #####################
#    ## realtime events

#    These are of no use in a midi file, so they are ignored!!!

#    def timing_clock(self):
#    def song_start(self):
#    def song_stop(self):
#    def song_continue(self):
#    def active_sensing(self):
#    def system_reset(self):



if __name__ == '__main__':

    out_file = 'test/midifiles/midiout.mid'
    midi = MidiOutFile(out_file)

#format: 0, nTracks: 1, division: 480
#----------------------------------
#
#Start - track #0
#sequence_name: Type 0
#tempo: 500000
#time_signature: 4 2 24 8
#note_on  - ch:00,  note:48,  vel:64 time:0
#note_off - ch:00,  note:48,  vel:40 time:480
#End of track
#
#End of file


    midi.header(0, 1, 480)
    
    midi.start_of_track()
    midi.sequence_name('Type 0')
    midi.tempo(750000)
    midi.time_signature(4, 2, 24, 8)
    ch = 0
    for i in range(127):
        midi.note_on(ch, i, 0x64)
        midi.update_time(96)
        midi.note_off(ch, i, 0x40)
        midi.update_time(0)
    
    midi.update_time(0)
    midi.end_of_track()
    
    midi.eof() # currently optional, should it do the write instead of write??


    midi.write()
