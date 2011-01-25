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

import time
import weakref
import popplerqt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *


_cache = weakref.WeakKeyDictionary()
_runners = weakref.WeakKeyDictionary()


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
            return _cache[document][pageKey][sizeKey][0]
        except KeyError:
            return
    try:
        sizes = _cache[document][pageKey].keys()
    except KeyError:
        return
    # find the closest size (assuming aspect ratio has not changed)
    if sizes:
        sizes.sort(key=lambda s: abs(1 - s[0] / float(page.width())))
        image = _cache[document][pageKey][sizes[0]][0]
        return image


def generate(page):
    """Generates an image for the cache."""
    # Poppler-Qt4 crashes when different pages from a Document are rendered at the same time,
    # so we schedule them to be run in sequence.
    document = page.document()
    try:
        runner = _runners[document]
    except KeyError:
        runner = _runners[document] = Runner()
    return runner.job(page)


def add(image, document, pageNumber, rotation, width, height):
    """Adds an image to the cache."""
    pageKey = (pageNumber, rotation)
    sizeKey = (width, height)
    _cache.setdefault(document, {}).setdefault(pageKey, {})[sizeKey] = (image, time.time())
    purge()


def purge():
    """Removes old images from the cache to limit the space used."""
    # make a list of the images, sorted on time
    images = []
    for doc, pageKeys in _cache.items():
        for pageKey, sizeKeys in pageKeys.items():
            for sizeKey, (image, time) in sizeKeys.items():
                images.append((time, doc, pageKey, sizeKey, image.byteCount()))
    # newest first
    images.sort(key = lambda i: i[0], reverse=True)
    
    
class Runner(object):
    """Manages running rendering jobs in sequence for a Document."""
    def __init__(self):
        self._schedule = []     # order
        self._jobs = {}         # jobs on key
        self._running = None
        
    def job(self, page):
        """Creates or returns an existing Job.
        
        The returned Job will be scheduled to run as the first one.
        
        """
        # uniquely identify the image to be generated
        key = (page.pageNumber(), page.rotation(), page.width(), page.height())
        try:
            job = self._jobs[key]
        except KeyError:
            job = self._jobs[key] = Job(page)
            job.key = key
        else:
            self._schedule.remove(job)
            job.notify(page)
        self._schedule.append(job)
        self.checkStart()
        return job
        
    def checkStart(self):
        if self._schedule and not self._running:
            job = self._schedule[-1]
            document = job.document()
            if document:
                self._running = Run(self, document, job)
            else:
                self.done(job)
            
    def done(self, job):
        del self._jobs[job.key]
        self._schedule.remove(job)
        self._running = None
        for page in job.pages():
            page.update()
        self.checkStart()



class Job(object):
    """Simply contains data needed to create an image later."""
    def __init__(self, page):
        self._pages = []
        self.document = weakref.ref(page.document())
        self.pageNumber = page.pageNumber()
        self.rotation = page.rotation()
        self.width = page.width()
        self.height = page.height()
        self.notify(page)
        
    def notify(self, page):
        pageref = weakref.ref(page)
        if pageref not in self._pages:
            self._pages.append(pageref)
        
    def pages(self):
        for pageref in self._pages:
            page = pageref()
            if page:
                yield page


class Run(QThread):
    """Immediately runs a Job, using a thread."""
    def __init__(self, runner, document, job):
        super(Run, self).__init__()
        self.runner = runner
        self.job = job
        self.document = document # keep reference now so that it does not die during this thread
        self.finished.connect(self.slotFinished)
        self.start()
        
    def run(self):
        page = self.document.page(self.job.pageNumber)
        pageSize = page.pageSize()
        if self.job.rotation & 1:
            pageSize.transpose()
        xres = 72.0 * self.job.width / pageSize.width()
        yres = 72.0 * self.job.height / pageSize.height()
        self.image = page.renderToImage(xres, yres, 0, 0, self.job.width, self.job.height, self.job.rotation)
        
    def slotFinished(self):
        add(self.image, self.document, self.job.pageNumber, self.job.rotation, self.job.width, self.job.height)
        self.runner.done(self.job)



