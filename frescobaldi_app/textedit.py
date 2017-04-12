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
Parse textedit:// urls.
"""


import re
import sys
import collections

__all__ = ['link', 'percent_decode']


textedit_match = re.compile(r"^textedit://(.*?):(\d+):(\d+)(?::\d+)$").match

Link = collections.namedtuple("Link", "filename line column")


def link(url):
    """Return Link(filename, line, column) for the specified `textedit:` url.

    Link is a named tuple (filename, line, column).
    If the url is not a valid textedit url, None is returned.

    The url should be specified as a normal Python string (unicode in Python 2,
    str in Python 3); the filename is percent-decoded and converted in the
    correct filesystem encoding if necessary.

    """
    m = textedit_match(url)
    if m:
        return readurl(m)

def readurl(match):
    """Return Link(filename, line, col) for the match object resulting from textedit_match.

    Link is a named tuple (filename, line, column).

    """
    return Link(readfilename(match), int(match.group(2)), int(match.group(3)))

def readfilename(match):
    """Return the filename from the match object resulting from textedit_match."""
    fname = match.group(1)
    lat1 = fname.encode('latin1')
    try:
        lat1 = percent_decode(lat1)
    except ValueError:
        pass
    try:
        fname = lat1.decode(sys.getfilesystemencoding())
    except UnicodeError:
        pass
    return fname

def percent_decode(s):
    """Percent-decodes all %HH sequences in the specified bytes string."""
    l = s.split(b'%')
    res = bytearray(l[0])
    for i in l[1:]:
        res.append(int(i[:2], 16))
        res.extend(i[2:])
    return res
