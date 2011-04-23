# -*- coding: ISO-8859-1 -*-

class MidiOutStream(object):


    """

    MidiOutstream is Basically an eventhandler. It is the most central
    class in the Midi library. You use it both for writing events to
    an output stream, and as an event handler for an input stream.

    This makes it extremely easy to take input from one stream and
    send it to another. Ie. if you want to read a Midi file, do some
    processing, and send it to a midiport.

    All time values are in absolute values from the opening of a
    stream. To calculate time values, please use the MidiTime and
    MidiDeltaTime classes.

    """

    def __init__(self):
        
        # the time is rather global, so it needs to be stored 
        # here. Otherwise there would be no really simple way to 
        # calculate it. The alternative would be to have each event 
        # handler do it. That sucks even worse!
        self._absolute_time = 0
        self._relative_time = 0
        self._current_track = 0
        self._running_status = None

    # time handling event handlers. They should be overwritten with care

    def update_time(self, new_time=0, relative=1):
        """
        Updates the time, if relative is true, new_time is relative, 
        else it's absolute.
        """
        if relative:
            self._relative_time = new_time
            self._absolute_time += new_time
        else:
            self._relative_time = new_time - self._absolute_time
            self._absolute_time = new_time

    def reset_time(self):
        """
        reset time to 0
        """
        self._relative_time = 0
        self._absolute_time = 0
        
    def rel_time(self):
        "Returns the relative time"
        return self._relative_time

    def abs_time(self):
        "Returns the absolute time"
        return self._absolute_time

    # running status methods
    
    def reset_run_stat(self):
        "Invalidates the running status"
        self._running_status = None

    def set_run_stat(self, new_status):
        "Set the new running status"
        self._running_status = new_status

    def get_run_stat(self):
        "Set the new running status"
        return self._running_status

    # track handling event handlers
    
    def set_current_track(self, new_track):
        "Sets the current track number"
        self._current_track = new_track
    
    def get_current_track(self):
        "Returns the current track number"
        return self._current_track
    
    
    #####################
    ## Midi events


    def channel_message(self, message_type, channel, data):
        """The default event handler for channel messages"""
        pass


    def note_on(self, channel=0, note=0x40, velocity=0x40):

        """
        channel: 0-15
        note, velocity: 0-127
        """
        pass


    def note_off(self, channel=0, note=0x40, velocity=0x40):

        """
        channel: 0-15
        note, velocity: 0-127
        """
        pass


    def aftertouch(self, channel=0, note=0x40, velocity=0x40):

        """
        channel: 0-15
        note, velocity: 0-127
        """
        pass


    def continuous_controller(self, channel, controller, value):

        """
        channel: 0-15
        controller, value: 0-127
        """
        pass


    def patch_change(self, channel, patch):

        """
        channel: 0-15
        patch: 0-127
        """
        pass


    def channel_pressure(self, channel, pressure):

        """
        channel: 0-15
        pressure: 0-127
        """
        pass


    def pitch_bend(self, channel, value):

        """
        channel: 0-15
        value: 0-16383

        """
        pass




    #####################
    ## System Exclusive

    def system_exclusive(self, data):

        """
        data: list of values in range(128)
        """
        pass


    #####################
    ## Common events

    def song_position_pointer(self, value):

        """
        value: 0-16383
        """
        pass


    def song_select(self, songNumber):

        """
        songNumber: 0-127
        """
        pass


    def tuning_request(self):

        """
        No values passed
        """
        pass

            
    def midi_time_code(self, msg_type, values):
        """
        msg_type: 0-7
        values: 0-15
        """
        pass


    #########################
    # header does not really belong here. But anyhoo!!!
    
    def header(self, format=0, nTracks=1, division=96):

        """
        format: type of midi file in [1,2]
        nTracks: number of tracks
        division: timing division
        """
        pass


    def eof(self):

        """
        End of file. No more events to be processed.
        """
        pass


    #####################
    ## meta events


    def meta_event(self, meta_type, data):
        
        """
        Handles any undefined meta events
        """
        pass


    def start_of_track(self, n_track=0):

        """
        n_track: number of track
        """
        pass


    def end_of_track(self):

        """
        n_track: number of track
        """
        pass


    def sequence_number(self, value):

        """
        value: 0-16383
        """
        pass


    def text(self, text):

        """
        Text event
        text: string
        """
        pass


    def copyright(self, text):

        """
        Copyright notice
        text: string
        """
        pass


    def sequence_name(self, text):

        """
        Sequence/track name
        text: string
        """
        pass


    def instrument_name(self, text):

        """
        text: string
        """
        pass


    def lyric(self, text):

        """
        text: string
        """
        pass


    def marker(self, text):

        """
        text: string
        """
        pass


    def cuepoint(self, text):

        """
        text: string
        """
        pass


    def midi_ch_prefix(self, channel):

        """
        channel: midi channel for subsequent data (deprecated in the spec)
        """
        pass


    def midi_port(self, value):

        """
        value: Midi port (deprecated in the spec)
        """
        pass


    def tempo(self, value):

        """
        value: 0-2097151
        tempo in us/quarternote
        (to calculate value from bpm: int(60,000,000.00 / BPM))
        """
        pass


    def smtp_offset(self, hour, minute, second, frame, framePart):

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
        pass



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
        pass



    def key_signature(self, sf, mi):

        """
        sf: is a byte specifying the number of flats (-ve) or sharps 
            (+ve) that identifies the key signature (-7 = 7 flats, -1 
            = 1 flat, 0 = key of C, 1 = 1 sharp, etc).
        mi: is a byte specifying a major (0) or minor (1) key.
        """
        pass



    def sequencer_specific(self, data):

        """
        data: The data as byte values
        """
        pass




    #####################
    ## realtime events

    def timing_clock(self):

        """
        No values passed
        """
        pass



    def song_start(self):

        """
        No values passed
        """
        pass



    def song_stop(self):

        """
        No values passed
        """
        pass



    def song_continue(self):

        """
        No values passed
        """
        pass



    def active_sensing(self):

        """
        No values passed
        """
        pass



    def system_reset(self):

        """
        No values passed
        """
        pass



if __name__ == '__main__':

    midiOut = MidiOutStream()
    midiOut.update_time(0,0)
    midiOut.note_on(0, 63, 127)
    midiOut.note_off(0, 63, 127)

