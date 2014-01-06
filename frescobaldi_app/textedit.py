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

from __future__ import unicode_literals

import re
import sys
import collections

import util
import percentcoding


textedit_match = re.compile(r"^textedit://(.*?):(\d+):(\d+)(?::\d+)$").match

Link = collections.namedtuple("Link", "filename line column")


def link(url):
    """Return Link(filename, line, column) for the url if it's valid.
    
    Link is a named tuple (filename, line, column).
    
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
        lat1 = percentcoding.decode(lat1)
    except ValueError:
        pass
    try:
        fname = lat1.decode(sys.getfilesystemencoding())
    except UnicodeError:
        pass
    # normalize path (although this might change a path if it contains
    # symlinks followed by '/../' !
    fname = util.normpath(fname)
    return fname

