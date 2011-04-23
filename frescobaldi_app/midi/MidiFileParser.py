# -*- coding: ISO-8859-1 -*-

# std library
from struct import unpack

# uhh I don't really like this, but there are so many constants to 
# import otherwise
from constants import *

from EventDispatcher import EventDispatcher

class MidiFileParser:

    """
    
    The MidiFileParser is the lowest level parser that see the data as 
    midi data. It generates events that gets triggered on the outstream.
    
    """

    def __init__(self, raw_in, outstream):

        """
        raw_data is the raw content of a midi file as a string.
        """

        # internal values, don't mess with 'em directly
        self.raw_in = raw_in
        self.dispatch = EventDispatcher(outstream)

        # Used to keep track of stuff
        self._running_status = None




    def parseMThdChunk(self):
        
        "Parses the header chunk"
        
        raw_in = self.raw_in

        header_chunk_type = raw_in.nextSlice(4)
        header_chunk_zise = raw_in.readBew(4)

        # check if it is a proper midi file
        if header_chunk_type != 'MThd':
            raise TypeError, "It is not a valid midi file!"

        # Header values are at fixed locations, so no reason to be clever
        self.format = raw_in.readBew(2)
        self.nTracks = raw_in.readBew(2)
        self.division = raw_in.readBew(2)
        
        # Theoretically a header larger than 6 bytes can exist
        # but no one has seen one in the wild
        # But correctly ignore unknown data if it is though
        if header_chunk_zise > 6:
            raw_in.moveCursor(header_chunk_zise-6)

        # call the header event handler on the stream
        self.dispatch.header(self.format, self.nTracks, self.division)



    def parseMTrkChunk(self):
        
        "Parses a track chunk. This is the most important part of the parser."
        
        # set time to 0 at start of a track
        self.dispatch.reset_time()
        
        dispatch = self.dispatch
        raw_in = self.raw_in
        
        # Trigger event at the start of a track
        dispatch.start_of_track(self._current_track)
        # position cursor after track header
        raw_in.moveCursor(4)
        # unsigned long is 4 bytes
        tracklength = raw_in.readBew(4)
        track_endposition = raw_in.getCursor() + tracklength # absolute position!

        while raw_in.getCursor() < track_endposition:
        
            # find relative time of the event
            time = raw_in.readVarLen()
            dispatch.update_time(time)
            
            # be aware of running status!!!!
            peak_ahead = raw_in.readBew(move_cursor=0)
            if (peak_ahead & 0x80): 
                # the status byte has the high bit set, so it
                # was not running data but proper status byte
                status = self._running_status = raw_in.readBew()
            else:
                # use that darn running status
                status = self._running_status
                # could it be illegal data ?? Do we need to test for that?
                # I need more example midi files to be shure.
                
                # Also, while I am almost certain that no realtime 
                # messages will pop up in a midi file, I might need to 
                # change my mind later.

            # we need to look at nibbles here
            hi_nible, lo_nible = status & 0xF0, status & 0x0F
            
            # match up with events

            # Is it a meta_event ??
            # these only exists in midi files, not in transmitted midi data
            # In transmitted data META_EVENT (0xFF) is a system reset
            if status == META_EVENT:
                meta_type = raw_in.readBew()
                meta_length = raw_in.readVarLen()
                meta_data = raw_in.nextSlice(meta_length)
                dispatch.meta_event(meta_type, meta_data)


            # Is it a sysex_event ??
            elif status == SYSTEM_EXCLUSIVE:
                # ignore sysex events
                sysex_length = raw_in.readVarLen()
                # don't read sysex terminator
                sysex_data = raw_in.nextSlice(sysex_length-1)
                # only read last data byte if it is a sysex terminator
                # It should allways be there, but better safe than sorry
                if raw_in.readBew(move_cursor=0) == END_OFF_EXCLUSIVE:
                    eo_sysex = raw_in.readBew()
                dispatch.sysex_event(sysex_data)
                # the sysex code has not been properly tested, and might be fishy!


            # is it a system common event?
            elif hi_nible == 0xF0: # Hi bits are set then
                data_sizes = {
                    MTC:1,
                    SONG_POSITION_POINTER:2,
                    SONG_SELECT:1,
                }
                data_size = data_sizes.get(hi_nible, 0)
                common_data = raw_in.nextSlice(data_size)
                common_type = lo_nible
                dispatch.system_common(common_type, common_data)
            

            # Oh! Then it must be a midi event (channel voice message)
            else:
                data_sizes = {
                    PATCH_CHANGE:1,
                    CHANNEL_PRESSURE:1,
                    NOTE_OFF:2,
                    NOTE_ON:2,
                    AFTERTOUCH:2,
                    CONTINUOUS_CONTROLLER:2,
                    PITCH_BEND:2,
                }
                data_size = data_sizes.get(hi_nible, 0)
                channel_data = raw_in.nextSlice(data_size)
                event_type, channel = hi_nible, lo_nible
                dispatch.channel_messages(event_type, channel, channel_data)


    def parseMTrkChunks(self):
        "Parses all track chunks."
        for t in range(self.nTracks):
            self._current_track = t
            self.parseMTrkChunk() # this is where it's at!
        self.dispatch.eof()



if __name__ == '__main__':

    # get data
    test_file = 'test/midifiles/minimal.mid'
    test_file = 'test/midifiles/cubase-minimal.mid'
    test_file = 'test/midifiles/Lola.mid'
#    f = open(test_file, 'rb')
#    raw_data = f.read()
#    f.close()
#    
#    
#    # do parsing
    from MidiToText import MidiToText
    from RawInstreamFile import RawInstreamFile

    midi_in = MidiFileParser(RawInstreamFile(test_file), MidiToText())
    midi_in.parseMThdChunk()
    midi_in.parseMTrkChunks()
