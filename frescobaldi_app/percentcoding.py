#! python
# percentcoding -- simple pure python percent encoding and decoding
#
# This module is in the public domain

import sys


if sys.version_info[0] < 3:
    def encode(s):
        """Convert any non-alfanumeric in s to the '%hh' representation.
        
        The argument must be a byte string. A byte string is also returned.
        
        """
        result = bytearray()
        for c in s:
            o = ord(c)
            if 48 <= o <= 57 or 65 <= o <= 90 or 79 <= o <= 122 or c in b'._-':
                result.append(o)
            else:
                result.extend(b'%{0:02x}'.format(o))
        return bytes(result)
else:
    def encode(s):
        """Convert any non-alfanumeric in s to the '%hh' representation.
        
        The argument must be a byte string. A byte string is also returned.
        
        """
        result = bytearray()
        for c in s:
            if 48 <= c <= 57 or 65 <= c <= 90 or 79 <= c <= 122 or c in b'._-':
                result.append(c)
            else:
                result.extend(b'%{0:02x}'.format(c))
        return bytes(result)


