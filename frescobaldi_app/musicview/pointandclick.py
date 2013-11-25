# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Handles Point and Click.
"""

from __future__ import unicode_literals
from __future__ import absolute_import

import re
import os
import sys
import weakref

import qpopplerview

import util
import pointandclick
import percentcoding


# cache point and click handlers for poppler documents
_cache = weakref.WeakKeyDictionary()

# parse textedit urls
textedit_match = re.compile(r"^textedit://(.*?):(\d+):(\d+)(?::\d+)$").match


def readfilename(match):
    """Returns the filename from the match object resulting from textedit_match."""
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


def readurl(match):
    """Returns filename, line, col for the match object resulting from textedit_match."""
    return readfilename(match), int(match.group(2)), int(match.group(3))


def links(document):
    try:
        return _cache[document]
    except KeyError:
        l = _cache[document] = Links()
        l.import_document(document)
        return l


class Links(pointandclick.Links):
    """Stores all the links of a Poppler document sorted by URL and text position.
    
    Only textedit:// urls are stored.
    
    """
    def import_document(self, document):
        import popplerqt4
        with qpopplerview.lock(document):
            for num in range(document.numPages()):
                page = document.page(num)
                for link in page.links():
                    if isinstance(link, popplerqt4.Poppler.LinkBrowse):
                        m = textedit_match(link.url())
                        if m:
                            filename, line, col = readurl(m)
                            self.add_link(filename, line, col, (num, link.linkArea()))
        self.finish()
    
    def cursor(self, link, load=False):
        """Returns the destination of a link as a QTextCursor of the destination document.
        
        If load (defaulting to False) is True, the document is loaded if it is not yet loaded.
        Returns None if the url was not valid or the document could not be loaded.
        
        """
        import popplerqt4
        if not isinstance(link, popplerqt4.Poppler.LinkBrowse) or not link.url():
            return
        m = textedit_match(link.url())
        if m:
            filename, line, col = readurl(m)
            return super(Links, self).cursor(filename, line, col, load)

