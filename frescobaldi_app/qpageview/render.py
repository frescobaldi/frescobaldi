# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2016 by Wilbert Berendsen
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
Infrastructure for rendering and caching Page images.
"""

import collections
import itertools
import weakref
import time

from PyQt5.QtCore import QRectF, Qt, QThread
from PyQt5.QtGui import QColor, QImage

from . import cache


cache_key = collections.namedtuple('cache_key', 'group page size')


# the maximum number of concurrent jobs (at global level)
maxjobs = 4

# we use a global dict to keep running jobs in, so a thread is never
# deallocated when a renderer dies.
_jobs = {}


class Job(QThread):
    image = None
    running = False
    def __init__(self, renderer, page):
        super().__init__()
        self.renderer = renderer
        self.page = page
        self.time = time.time()
        self.callbacks = set()
        self.finished.connect(self._slotFinished)

    def start(self):
        self.page_copy = self.page.copy()
        self.key = self.renderer.key(self.page)
        self.running = True
        super().start()

    def run(self):
        self.image = self.renderer.render(self.page_copy)

    def _slotFinished(self):
        self.renderer.finish(self)


class AbstractImageRenderer:
    """Handle rendering and caching of images.

    A renderer can be assigned to the renderer attribute of a Page and takes
    care for generating, caching and updating the images needed for display
    of the Page at different sizes.

    You can use a renderer for as many Page instances as you like. You can use
    one global renderer in your application or more, depending on how you use
    the qpageview package.

    You must inherit from this class and at least implement the
    render() method.

    Instance attributes:

        `paperColor`    Paper color. If possible this background color is used
                        when rendering the pages, also for temporary drawings
                        when a page has to be rendered. If None, Qt.white is
                        used. If a Page specifies its own paperColor, that color
                        prevails.


    """

    # default paper color to use (if possible, and when drawing an empty page)
    paperColor = QColor(Qt.white)

    def __init__(self):
        self.cache = cache.ImageCache()

    def key(self, page):
        """Return a cache_key instance for this Page.

        The cache_key is a four-tuple:

            group       = an object a weak reference is taken to. It could be
                          a document or some other structure the page belongs to.
                          By default the Page object itself is used.

            page        = the rotation by default, but if you use group differently,
                          you should use here a hashable object that identifies
                          the page in the group.

            size        = must be the (width, height) tuple of the page.

        The cache_key is used to store and find back requests and to cache
        results.

        """
        return cache_key(
            page,
            page.computedRotation,
            (page.width, page.height))

    def render(self, page):
        """Reimplement this method to generate an image for this Page."""
        return QImage()

    def paint(self, page, painter, rect, callback=None):
        """Paint a page.

        The Page calls this method by default in the paint() method.
        This method tries to fetch an image from the cache and paint that.
        If no image is available, render() is called in the background to
        generate one. If it is ready, the callback is called with the Page
        as argument. An interim image may be painted in the meantime (e.g.
        scaled from another size).

        """
        key = self.key(page)
        try:
            image = self.cache[key]
        except KeyError:
            image = self.cache.closest(key)
            if image:
                hscale = image.width() / page.width
                vscale = image.height() / page.height
                image_rect = QRectF(rect.x() * hscale, rect.y() * vscale,
                                    rect.width() * hscale, rect.height() * vscale)
                painter.drawImage(QRectF(rect), image, image_rect)
            else:
                color = page.paperColor or self.paperColor or QColor(Qt.white)
                painter.fillRect(rect, color)
            self.schedule(page, painter, callback)
        else:
            painter.drawImage(rect, image, rect)

    def schedule(self, page, painter, callback):
        """Start a new rendering job."""
        try:
            job = _jobs.setdefault(self, {})[page]
        except KeyError:
            job = _jobs[self][page] = Job(self, page)
        job.callbacks.add(callback)
        self.checkstart()

    def unschedule(self, page, callback):
        """Unschedule a possible pending rendering job.

        A rendering job is only removed if the specified callback was the only
        callback to call.

        """
        try:
            job = _jobs[self][page]
        except KeyError:
            return
        if not job.running:
            job.callbacks.discard(callback)
            if not job.callbacks:
                del _jobs[self][page]
                if not _jobs[self]:
                    del _jobs[self]

    def checkstart(self):
        """Check whether there are jobs that need to be started."""
        try:
            ourjobs = _jobs[self].values()
        except KeyError:
            return
        # count the total number of running jobs
        runningjobs = [j for jobs in _jobs.values()
                         for j in jobs.values() if j.running]
        waitingjobs = sorted((j for j in ourjobs if not j.running),
                             key=lambda j: j.time, reverse=True)
        jobcount = len(runningjobs)

        for job in waitingjobs[:maxjobs-jobcount]:
            mutex = job.page.mutex()
            if mutex is None or not any(mutex is j.page.mutex() for j in runningjobs):
                runningjobs.append(job)
                job.start()

    def finish(self, job):
        """Called by the job when finished."""
        self.cache[job.key] = job.image
        # if page already was resized during rendering, immediately rerender...
        if job.page.size() != job.page_copy.size():
            job.start()
        else:
            for cb in job.callbacks:
                cb(job.page)
            del _jobs[self][job.page]
            if not _jobs[self]:
                del _jobs[self]
            else:
                self.checkstart()

