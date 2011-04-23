# -*- coding: ISO-8859-1 -*-

# standard library imports
from types import StringType
from struct import unpack

# custom import
from DataTypeConverters import readBew, readVar, varLen


class RawInstreamFile:
    
    """
    
    It parses and reads data from an input file. It takes care of big 
    endianess, and keeps track of the cursor position. The midi parser 
    only reads from this object. Never directly from the file.
    
    """
    
    def __init__(self, infile=''):
        """ 
        If 'file' is a string we assume it is a path and read from 
        that file.
        If it is a file descriptor we read from the file, but we don't 
        close it.
        Midi files are usually pretty small, so it should be safe to 
        copy them into memory.
        """
        if infile:
            if isinstance(infile, StringType):
                infile = open(infile, 'rb')
                self.data = infile.read()
                infile.close()
            else:
                # don't close the f
                self.data = infile.read()
        else:
            self.data = ''
        # start at beginning ;-)
        self.cursor = 0


    # setting up data manually
    
    def setData(self, data=''):
        "Sets the data from a string."
        self.data = data
    
    # cursor operations

    def setCursor(self, position=0):
        "Sets the absolute position if the cursor"
        self.cursor = position


    def getCursor(self):
        "Returns the value of the cursor"
        return self.cursor
        
        
    def moveCursor(self, relative_position=0):
        "Moves the cursor to a new relative position"
        self.cursor += relative_position

    # native data reading functions
        
    def nextSlice(self, length, move_cursor=1):
        "Reads the next text slice from the raw data, with length"
        c = self.cursor
        slc = self.data[c:c+length]
        if move_cursor:
            self.moveCursor(length)
        return slc
        
        
    def readBew(self, n_bytes=1, move_cursor=1):
        """
        Reads n bytes of date from the current cursor position.
        Moves cursor if move_cursor is true
        """
        return readBew(self.nextSlice(n_bytes, move_cursor))


    def readVarLen(self):
        """
        Reads a variable length value from the current cursor position.
        Moves cursor if move_cursor is true
        """
        MAX_VARLEN = 4 # Max value varlen can be
        var = readVar(self.nextSlice(MAX_VARLEN, 0))
        # only move cursor the actual bytes in varlen
        self.moveCursor(varLen(var))
        return var



if __name__ == '__main__':

    test_file = 'test/midifiles/minimal.mid'
    fis = RawInstreamFile(test_file)
    print fis.nextSlice(len(fis.data))

    test_file = 'test/midifiles/cubase-minimal.mid'
    cubase_minimal = open(test_file, 'rb')
    fis2 = RawInstreamFile(cubase_minimal)
    print fis2.nextSlice(len(fis2.data))
    cubase_minimal.close()
