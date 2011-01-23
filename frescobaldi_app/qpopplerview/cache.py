# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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
Caching of generated images.
"""

import weakref
import popplerqt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *

_cache = weakref.WeakKeyDictionary()


def clear(document=None):
    if document:
        try:
            del _cache[document]
        except KeyError:
            pass
    else:
        _cache.clear()


def image(document, pageNumber, size, rotation=popplerqt4.Poppler.Page.Rotate0):
    """Returns a rendered image in size."""
    key = (pageNumber, size.width(), size.height(), rotation)
    try:
        return _cache[document][key]
    except KeyError:
        page = document.page(pageNumber)
        pageSize = page.pageSize()
        if rotation & 1:
            pageSize.transpose()
        xres = 72.0 * size.width() / pageSize.width()
        yres = 72.0 * size.height() / pageSize.height()
        image = page.renderToImage(xres, yres, 0, 0, size.width(), size.height(), rotation)
        _cache.setdefault(document, {})[key] = image
        return image


