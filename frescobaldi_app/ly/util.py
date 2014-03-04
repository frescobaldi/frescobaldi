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
Utility functions.
"""

from __future__ import unicode_literals

import string


_nums = (
    '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen',
    'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen')

_tens = (
    'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty',
    'Ninety')

def int2text(number):
    """Converts an integer to the English language name of that integer.
    
    E.g. converts 1 to "One". Supports numbers 0 to 999999.
    This can be used in LilyPond identifiers (that do not support digits).
    
    """
    result = []
    if number >= 1000:
        hundreds, number = divmod(number, 1000)
        result.append(int2text(hundreds) + "Thousand")
    if number >= 100:
        tens, number = divmod(number, 100)
        result.append(_nums[tens] + "Hundred")
    if number < 20:
        result.append(_nums[number])
    else:
        tens, number = divmod(number, 10)
        result.append(_tens[tens-2] + _nums[number])
    text = "".join(result)
    return text or 'Zero'


# Thanks: http://billmill.org/python_roman.html
_roman_numerals = (("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
("C", 100),("XC", 90),("L", 50),("XL", 40), ("X", 10), ("IX", 9), ("V", 5),
("IV", 4), ("I", 1))

def int2roman(n):
    if n < 1:
        raise ValueError('Roman numerals must be positive integers, got %s' % n)
    roman = []
    for ltr, num in _roman_numerals:
        k, n = divmod(n, num)
        roman.append(ltr * k)
    return "".join(roman)


def int2letter(number, chars=string.ascii_uppercase):
    """Converts an integer to one or more letters.
    
    E.g. 1 -> A, 2 -> B, ... 26 -> Z, 27 -> AA, etc.
    Zero returns the empty string.
    
    chars is the string to pick characters from, defaulting to
    string.ascii_uppercase.
    
    """
    mod = len(chars)
    result = []
    while number > 0:
        number, c = divmod(number - 1, mod)
        result.append(c)
    return "".join(chars[c] for c in reversed(result))


def mkid(*args):
    """Makes a lower-camel-case identifier of the strings in args.
    
    All strings are concatenated with the first character of every string
    uppercased, except for the first character, which is lowercased.
    
    Examples:
    mkid("Violin") ==> "violin"
    mkid("soprano", "verse") ==> "sopranoVerse"
    mkid("scoreOne", "choirII") ==> "scoreOneChoirII"
    
    """
    result = []
    for a in args[:1]:
        result.append(a[:1].lower())
        result.append(a[1:])
    for a in args[1:]:
        result.append(a[:1].upper())
        result.append(a[1:])
    return "".join(result)


