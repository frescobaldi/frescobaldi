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
_jobs = {}


def clear(document=None):
    if document:
        try:
            del _cache[document]
        except KeyError:
            pass
    else:
        _cache.clear()


def image(page, exact=True):
    """Returns a rendered image for given Page if in cache.
    
    If exact is True (default), the function returns None if the exact size was
    not in the cache. If exact is False, the function may return a temporary
    rendering of the page scaled from a different size, if that was available.
    
    """
    document = page.document()
    pageKey = (page.pageNumber(), page.rotation())
    sizeKey = (page.width(), page.height())
    
    if exact:
        try:
            return _cache[document][pageKey][sizeKey]
        except KeyError:
            return
    try:
        sizes = _cache[document][pageKey].keys()
    except KeyError:
        return
    # find the closest size (assuming aspect ratio has not changed) and cache that for the time being
    if sizes:
        sizes.sort(key=lambda s: abs(1 - s[0] / float(page.width())))
        image = _cache[document][pageKey][sizeKey] = _cache[document][pageKey][sizes[0]].scaled(page.size())
        return image



def gen(page):
    """Generates an image for the cache."""
    
    document = page.document()
    
    key = (document, page.pageNumber(), page.rotation(), page.width(), page.height())

    try:
        job = _jobs[key]
    except KeyError:
        job = Job(key)
        job.start()
    return job



class Job(QThread):
    
    done = pyqtSignal()
    
    def __init__(self, key):
        super(Job, self).__init__()
        _jobs[key] = self
        self._pages = []
        self._key = key
        self.finished.connect(self.slotFinished)
        print "Starting Job"

    def run(self):
        document, pageNumber, rotation, width, height = self._key
        page = document.page(pageNumber)
        pageSize = page.pageSize()
        if rotation & 1:
            pageSize.transpose()
        xres = 72.0 * width / pageSize.width()
        yres = 72.0 * height / pageSize.height()
        self._image = page.renderToImage(xres, yres, 0, 0, width, height, rotation)
        
    def slotFinished(self):
        document, pageNumber, rotation, width, height = self._key
        pageKey = (pageNumber, rotation)
        sizeKey = (width, height)
        _cache.setdefault(document, {}).setdefault(pageKey, {})[sizeKey] = self._image
        del _jobs[self._key]
        self.done.emit()
        print "Ending Job"
    

