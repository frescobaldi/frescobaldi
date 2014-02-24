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
LilyPond information and logic concerning durations
"""

from __future__ import unicode_literals


from fractions import Fraction


durations = [
    '\\maxima', '\\longa', '\\breve',
    '1', '2', '4', '8', '16', '32', '64', '128', '256', '512', '1024', '2048'
]


def tostring(dur, dots=0, factor=1):
    """Returns the LilyPond string representation of a given logarithmic duration.
    
    Supports values from -3 upto and including 11.
    -2 = '\\longa', 0  = '1' (whole note), etc.
    
    Adds the number of dots (defaults to 0) and the fraction factor if given.
    
    """
    s = durations[dur + 3] + '.' * dots
    if factor != 1:
        s += '*{0}'.format(factor)
    return s


def base_scaling(tokens):
    """Return (base, scaling) as two Fractions for the list of tokens."""
    base = Fraction(8, 1 << durations.index(tokens[0]))
    scaling = Fraction(1)
    half = base
    for t in tokens[1:]:
        if t == '.':
            half /= 2
            base += half
        elif t.startswith('*'):
            scaling *= Fraction(t[1:])
    return base, scaling


def base_scaling_string(duration):
    """Return (base, scaling) as two Fractions for the specified string."""
    items = duration.split('*')
    dots = items[0].split('.')
    base = Fraction(8, 1 << durations.index(dots[0].strip()))
    scaling = Fraction(1)
    half = base
    for dot in dots[1:]:
        half /= 2
        base += half
    for f in items[1:]:
        scaling *= Fraction(f.strip())
    return base, scaling


def fraction(tokens):
    """Return the duration of the Duration tokens as a Fraction."""
    base, scaling = base_scaling(tokens)
    return base * scaling


def fraction_string(duration):
    """Return the duration of the specified string as a Fraction."""
    base, scaling = base_scaling_string(duration)
    return base * scaling


def format_fraction(value):
    """Format the value as "5/1" etc."""
    if value == 0:
        return "0"
    elif isinstance(value, Fraction):
        return "{0}/{1}".format(value.numerator, value.denominator)
    else:
        return "{0}/1".format(value)


