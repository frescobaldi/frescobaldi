# -*- coding: ISO-8859-1 -*-

from RawInstreamFile import RawInstreamFile
from MidiFileParser import MidiFileParser


class MidiInFile:

    """
    
    Parses a midi file, and triggers the midi events on the outStream 
    object.
    
    Get example data from a minimal midi file, generated with cubase.
    >>> test_file = 'C:/Documents and Settings/maxm/Desktop/temp/midi/src/midi/tests/midifiles/minimal-cubase-type0.mid'
    
    Do parsing, and generate events with MidiToText,
    so we can see what a minimal midi file contains
    >>> from MidiToText import MidiToText
    >>> midi_in = MidiInFile(MidiToText(), test_file)
    >>> midi_in.read()
    format: 0, nTracks: 1, division: 480
    ----------------------------------
    <BLANKLINE>
    Start - track #0
    sequence_name: Type 0
    tempo: 500000
    time_signature: 4 2 24 8
    note_on  - ch:00,  note:48,  vel:64 time:0
    note_off - ch:00,  note:48,  vel:40 time:480
    End of track
    <BLANKLINE>
    End of file
    
    
    """

    def __init__(self, outStream, infile):
        # these could also have been mixins, would that be better? Nah!
        self.raw_in = RawInstreamFile(infile)
        self.parser = MidiFileParser(self.raw_in, outStream)


    def read(self):
        "Start parsing the file"
        p = self.parser
        p.parseMThdChunk()
        p.parseMTrkChunks()


    def setData(self, data=''):
        "Sets the data from a plain string"
        self.raw_in.setData(data)
    
    
