# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Encode and decode LilyPond (and other) plain text formats.
"""

from __future__ import unicode_literals

import codecs

import variables


def get_bom(data):
    """Get the BOM mark of data, if any.
    
    A two-tuple is returned (encoding, data). If the data starts with a BOM 
    mark, its encoding is determined and the BOM mark is stripped off. 
    Otherwise, the returned encoding is None and the data is returned 
    unchanged.
    
    """
    for bom, encoding in (
            (codecs.BOM_UTF8, 'utf-8'),
            (codecs.BOM_UTF16_LE, 'utf_16_le'),
            (codecs.BOM_UTF16_BE, 'utf_16_be'),
            (codecs.BOM_UTF32_LE, 'utf_32_le'),
            (codecs.BOM_UTF32_BE, 'utf_32_be'),
            ):
        if data.startswith(bom):
            return encoding, data[len(bom):]
    return None, data


def decode(data, encoding=None):
    """Decode binary data, using encoding if specified.
    
    When the encoding can't be determined and isn't specified, it is tried to 
    get the encoding from the document variables (see variables module).
    
    Otherwise utf-8 and finally latin1 are tried.
    
    """
    enc, data = get_bom(data)
    for e in (enc, encoding):
        if e:
            try:
                return data.decode(enc)
            except (UnicodeError, LookupError):
                pass
    latin1 = data.decode('latin1') # this never fails
    encoding = variables.variables(latin1).get("coding")
    for e in (encoding, 'utf-8'):
        if e and e != 'latin1':
            try:
                return data.decode(encoding)
            except (UnicodeError, LookupError):
                pass
    return latin1


def encode(text, encoding=None, default_encoding='utf-8'):
    """Return the bytes representing the text, encoded.
    
    Looks at the specified encoding or the 'coding' variable to determine 
    the encoding, otherwise falls back to the given default encoding, 
    defaulting to 'utf-8'.
    
    """
    enc = encoding or variables.variables(text).get("coding")
    if enc:
        try:
            return text.encode(encoding)
        except (LookupError, UnicodeError):
            pass
    return text.encode(default_encoding)


