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


durations = [
    '\\maxima', '\\longa', '\\breve',
    '1', '2', '4', '8', '16', '32', '64', '128', '256', '512', '1024', '2048'
]


def duration(dur, dots=0, factor=1):
    """Returns the LilyPond string representation of a given logarithmic duration.
    
    Supports values from -3 upto and including 11.
    -2 = '\\longa', 0  = '1' (whole note), etc.
    
    Adds the number of dots (defaults to 0) and the fraction factor if given.
    
    """
    s = durations[dur + 3] + '.' * dots
    if factor != 1:
        s += '*{0}'.format(factor)
    return s



