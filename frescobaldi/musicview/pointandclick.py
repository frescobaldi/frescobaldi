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
Handles Point and Click.
"""



import weakref

import qpageview.locking

import util
import textedit
import pointandclick

from PyQt6.QtCore import QPointF, QRectF


# cache point and click handlers for PDF documents
_cache = weakref.WeakKeyDictionary()


def links(document):
    # the backend object is replaced on every load
    # of the pdf, which makes it a suitable cache key
    key = document.document()

    try:
        return _cache[key]
    except KeyError:
        l = _cache[key] = Links()
        with l:
            with qpageview.locking.lock(document):
                for num, page in enumerate(document.pages()):
                    for link in page.links():
                        t = textedit.link(link.url)
                        if t:
                            filename = util.normpath(t.filename)
                            area = QRectF(QPointF(*link.area[0:2]), QPointF(*link.area[2:4]))
                            l.add_link(filename, t.line, t.column, (num, area))
        return l


class Links(pointandclick.Links):
    """Stores all the links of a PDF document sorted by URL and text position.

    Only textedit:// urls are stored.

    """
    def cursor(self, link, load=False):
        """Returns the destination of a link as a QTextCursor of the destination document.

        If load (defaulting to False) is True, the document is loaded if it is not yet loaded.
        Returns None if the url was not valid or the document could not be loaded.

        """
        import qpageview.link
        if not isinstance(link, qpageview.link.Link) or not link.url:
            return
        t = textedit.link(link.url)
        if t:
            filename = util.normpath(t.filename)
            return super().cursor(filename, t.line, t.column, load)


positions = pointandclick.positions


