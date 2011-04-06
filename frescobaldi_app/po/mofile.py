# a loader for MO files
# Heavily inspired by the Python gettext library, but allows for reading
# all contents of a MO file, also the msgid2's, which are not needed
# for translating but are useful when checking messages and translations
# for wrong Python variable fields.

from struct import unpack

LE_MAGIC = 0x950412deL
BE_MAGIC = 0xde120495L


def parse_mo(buf):
    """Parses the given buffer (a bytes instance) as a MO file.
    
    Yields raw message/translation pairs, not decoded or handled in any other way.
    
    """
    # are we LE or BE?
    magic = unpack('<I', buf[:4])[0]
    if magic == LE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
        ii = '<II'
    elif magic == BE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
        ii = '>II'
    else:
        raise IOError(0, 'Invalid MO data')
    
    buflen = len(buf)
    
    # read the MO buffer and store all data
    for i in range(msgcount):
        mlen, moff = unpack(ii, buf[masteridx:masteridx+8])
        mend = moff + mlen
        tlen, toff = unpack(ii, buf[transidx:transidx+8])
        tend = toff + tlen
        if mend < buflen and tend < buflen:
            msg = buf[moff:mend]
            tmsg = buf[toff:tend]
        else:
            raise IOError(0, 'Corrupt MO data')
        yield msg, tmsg
        masteridx += 8
        transidx += 8


def parse_header(data):
    """Parses the "header" (the msgstr of the first, empty, msgid) and returns it as a dict.
    
    The names are made lower-case.
    
    """
    info = {}
    lastkey = key = None
    for line in data.splitlines():
        line = line.strip()
        if line:
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip().lower()
                val = val.strip()
                info[key] = val
                lastkey = key
            elif lastkey:
                info[lastkey] += '\n' + line
    return info


