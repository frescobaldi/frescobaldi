# -*- coding: ISO-8859-1 -*-

from struct import pack, unpack

"""
This module contains functions for reading and writing the special data types
that a midi file contains.
"""

"""
nibbles are four bits. A byte consists of two nibles.
hiBits==0xF0, loBits==0x0F Especially used for setting
channel and event in 1. byte of musical midi events
"""



def getNibbles(byte):
    """
    Returns hi and lo bits in a byte as a tuple
    >>> getNibbles(142)
    (8, 14)
    
    Asserts byte value in byte range
    >>> getNibbles(256)
    Traceback (most recent call last):
        ...
    ValueError: Byte value out of range 0-255: 256
    """
    if not 0 <= byte <= 255:
        raise ValueError('Byte value out of range 0-255: %s' % byte)
    return (byte >> 4 & 0xF, byte & 0xF)


def setNibbles(hiNibble, loNibble):
    """
    Returns byte with value set according to hi and lo bits
    Asserts hiNibble and loNibble in range(16)
    >>> setNibbles(8, 14)
    142
    
    >>> setNibbles(8, 16)
    Traceback (most recent call last):
        ...
    ValueError: Nible value out of range 0-15: (8, 16)
    """
    if not (0 <= hiNibble <= 15) or not (0 <= loNibble <= 15):
        raise ValueError('Nible value out of range 0-15: (%s, %s)' % (hiNibble, loNibble))
    return (hiNibble << 4) + loNibble



def readBew(value):
    """
    Reads string as big endian word, (asserts len(value) in [1,2,4])
    >>> readBew('aáâã')
    1642193635L
    >>> readBew('aá')
    25057
    """
    return unpack('>%s' % {1:'B', 2:'H', 4:'L'}[len(value)], value)[0]


def writeBew(value, length):
    """
    Write int as big endian formatted string, (asserts length in [1,2,4])
    Difficult to print the result in doctest, so I do a simple roundabout test.
    >>> readBew(writeBew(25057, 2))
    25057
    >>> readBew(writeBew(1642193635L, 4))
    1642193635L
    """
    return pack('>%s' % {1:'B', 2:'H', 4:'L'}[length], value)



"""
Variable Length Data (varlen) is a data format sprayed liberally throughout
a midi file. It can be anywhere from 1 to 4 bytes long.
If the 8'th bit is set in a byte another byte follows. The value is stored
in the lowest 7 bits of each byte. So max value is 4x7 bits = 28 bits.
"""


def readVar(value):
    """
    Converts varlength format to integer. Just pass it 0 or more chars that
    might be a varlen and it will only use the relevant chars.
    use varLen(readVar(value)) to see how many bytes the integer value takes.
    asserts len(value) >= 0
    >>> readVar('€@')
    64
    >>> readVar('áâãa')
    205042145
    """
    sum = 0
    for byte in unpack('%sB' % len(value), value):
        sum = (sum << 7) + (byte & 0x7F)
        if not 0x80 & byte: break # stop after last byte
    return sum



def varLen(value):
    """
    Returns the the number of bytes an integer will be when
    converted to varlength
    """
    if value <= 127:
        return 1
    elif value <= 16383:
        return 2
    elif value <= 2097151:
        return 3
    else:
        return 4


def writeVar(value):
    "Converts an integer to varlength format"
    sevens = to_n_bits(value, varLen(value))
    for i in range(len(sevens)-1):
        sevens[i] = sevens[i] | 0x80
    return fromBytes(sevens)


def to_n_bits(value, length=1, nbits=7):
    "returns the integer value as a sequence of nbits bytes"
    bytes = [(value >> (i*nbits)) & 0x7F for i in range(length)]
    bytes.reverse()
    return bytes


def toBytes(value):
    "Turns a string into a list of byte values"
    return unpack('%sB' % len(value), value)


def fromBytes(value):
    "Turns a list of bytes into a string"
    if not value:
        return ''
    return pack('%sB' % len(value), *value)



if __name__ == '__main__':

#    print to7bits(0, 3)
#    print to7bits(127, 3)
#    print to7bits(255, 3)
#    print to7bits(65536, 3)

    # simple test cases
    
#    print 'getHiLoHex', getNibbles(16)
#    print 'setHiLoHex', setNibbles(1,0)
#    
#    print 'readBew', readBew('aáâã')
#    print 'writeBew', writeBew(1642193635, 4)
#
#    print 'varLen', varLen(1)
#
    print 'readVar', readVar('€@')
    print 'writeVar', writeVar(8192)
    
    print 'readVar', readVar('áâãa')
    print 'writeVar', writeVar(205058401)
#    
#    vartest = '\x82\xF7\x80\x00'
#    print 'toBytes', toBytes(vartest)
#    print 'fromBytes', fromBytes([48, 49, 50,])
    
    
#    instr = '\xFF\xFF\xFF\x00'
#    print 'readVar', readVar(instr)
#    inst2 = 268435455
#    print inst2
#    print writeVar(inst2)
#    print writeVar(readVar(instr))

    s1 = 0x00000000
    print '%08X -' % s1, '00',  writeVar(s1)
    s2 = 0x00000040
    print '%08X -' % s2, '40',  writeVar(s2)
    s3 = 0x0000007F
    print '%08X -' % s3, '7F',  writeVar(s3)
    s4 = 0x00000080
    print '%08X -' % s4, '81 00',  writeVar(s4)
    s5 = 0x00002000
    print '%08X -' % s5, 'C0 00',  writeVar(s5)
    s6 = 0x00003FFF
    print '%08X -' % s6, 'FF 7F',  writeVar(s6)
    s7 = 0x00004000
    print '%08X -' % s7, '81 80 00',  writeVar(s7)
    s8 = 0x00100000
    print '%08X -' % s8, 'C0 80 00',  writeVar(s8)
    s9 = 0x001FFFFF
    print '%08X -' % s9, 'FF FF 7F',  writeVar(s9)
    s10 = 0x00200000
    print '%08X -' % s10, '81 80 80 00', writeVar(s10)
    s11 = 0x08000000
    print '%08X -' % s11, 'C0 80 80 00', writeVar(s11)
    s12 = 0x0FFFFFFF
    print '%08X -' % s12, 'FF FF FF 7F', writeVar(s12)
              
              
              
             
             
             
           
           
           
          
          
