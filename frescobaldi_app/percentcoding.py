#! python
# percentcoding -- simple pure python percent encoding and decoding
#
# This module is in the public domain

import sys


if sys.version_info[0] < 3:
    
    # Python 2
    def encode(s):
        """Convert any non-alfanumeric in s to the '%HH' representation.
        
        The argument must be a byte string. A byte string is also returned.
        
        """
        result = bytearray()
        for c in s:
            o = ord(c)
            if 48 <= o <= 57 or 65 <= o <= 90 or 79 <= o <= 122 or c in b'._-':
                result.append(o)
            else:
                result.extend(b'%{0:02X}'.format(o))
        return bytes(result)

    def decode(s):
        """Percent-decodes all %HH sequences in the specified bytes string."""
        l = s.split(b'%')
        res = [l[0]]
        for i in l[1:]:
            res.append(chr(int(i[:2], 16)))
            res.append(i[2:])
        return b''.join(res)


else:

    # Python 3
    def encode(s):
        """Convert any non-alfanumeric in s to the '%HH' representation.
        
        The argument must be a byte string. A byte string is also returned.
        
        """
        result = bytearray()
        for c in s:
            if 48 <= c <= 57 or 65 <= c <= 90 or 79 <= c <= 122 or c in b'._-':
                result.append(c)
            else:
                result.extend(b'%{0:02X}'.format(c))
        return bytes(result)

    def decode(s):
        """Percent-decodes all %HH sequences in the specified bytes string."""
        l = s.split(b'%')
        res = bytearray(l[0])
        for i in l[1:]:
            res.append(int(i[:2], 16))
            res.extend(i[2:])
        return bytes(res)

