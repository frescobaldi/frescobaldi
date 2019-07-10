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

import itertools
import weakref
import time

from PyQt5.QtCore import QRect, QRectF, Qt, QThread
from PyQt5.QtGui import QColor, QImage

from . import cache


# the maximum number of concurrent jobs (at global level)
maxjobs = 4

# we use a global dict to keep running jobs in, so a thread is never
# deallocated when a renderer dies.
_jobs = {}


class Job(QThread):
    """A simple wrapper around QThread.
    
    Job is instantiated with the Page to render and the Renderer to use.
    As soon as start() is called, a copy is made of the Page object, so that
    a change of the Page's dimensions during rendering is noticed.
    
    You don't need to instantiate Job objects, that is done by the schedule()
    method of AbstractImageRenderer.
    
    """
    image = None
    running = False
    def __init__(self, renderer, key):
        super().__init__()
        self.renderer = renderer
        self.key = key
        self.running = False
        self.time = time.time()
        self.callbacks = set()
        self.finished.connect(self._slotFinished)

    def start(self):
        """Start rendering in the background."""
        self.running = True
        super().start()

    def run(self):
        """This is called in the background thread by Qt."""
        self.image = self.renderer.render(self.key)

    def _slotFinished(self):
        self.running = False
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
    
    def group(self, page):
        """Return the group the page belongs to.
        
        This could be some document structure, so that different Page objects
        could refer to the same graphical contents, preventing double caching.
        
        By default, the page object itself is returned.
        """
        return page
        
    def ident(self, page):
        """Return a value that identifies the page within the group returned
        by group().
        
        By default, None is returned.
        """
        return None
    
    def key(self, page, pixelratio):
        """Return a key under which the image for this page at the specified
        pixel ratio can be cached.
        
        The key is a named tuple: page, group, ident, width, height, rotation
        
        """
        return cache.cache_key(
            page,
            self.group(page),
            self.ident(page),
            page.width * pixelratio,
            page.height * pixelratio,
            page.computedRotation,
        )
        
        
    def render(self, key):
        """Reimplement this method to generate a QImage for this Page."""
        return QImage()
    
    def paint(self, page, painter, rect, callback=None):
        """Paint a page.
        
        page: the Page to draw

        painter:  the QPainter to use to draw
        
        rect: the region to draw
        
        callback: if specified, a callable accepting the `page` argument.
        Typically this should be used to trigger a repaint of the view.
        
        The Page calls this method by default in the paint() method.
        This method tries to fetch an image from the cache and paint that.
        If no image is available, render() is called in the background to
        generate one. If it is ready, the callback is called with the Page
        as argument. An interim image may be painted in the meantime (e.g.
        scaled from another size).

        """
        ### TODO:
        ### * if a page is enlarged very much, use tiles to render and cache
        ###   the images
        
        ratio = painter.device().devicePixelRatioF()
        key = self.key(page, ratio)
        try:
            image = self.cache[key]
        except KeyError:
            image = self.cache.closest(key)
            if image:
                hscale = image.width() / key.width
                vscale = image.height() / key.height
                image_rect = QRectF(rect.x() * hscale, rect.y() * vscale,
                                    rect.width() * hscale, rect.height() * vscale)
                painter.drawImage(QRectF(rect), image, image_rect)
            else:
                color = page.paperColor or self.paperColor or QColor(Qt.white)
                painter.fillRect(rect, color)
            self.schedule(key, callback)
        else:
            image_rect = QRect(rect.x() * ratio, rect.y() * ratio,
                               rect.width() * ratio, rect.height() * ratio)
            painter.drawImage(rect, image, image_rect)

    def schedule(self, key, callback):
        """Schedule a new rendering job.
        
        If this page has already a job pending, the callback is added to the
        pending job.
        
        """
        try:
            job = _jobs.setdefault(self, {})[key.page]
        except KeyError:
            job = _jobs[self][key.page] = Job(self, key)
        job.callbacks.add(callback)
        self.checkstart()

    def unschedule(self, page, callback):
        """Unschedule a possible pending rendering job.

        If the pending job has no other callbacks left, it is removed.

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
        """Check whether there are jobs that need to be started.
        
        This method is called by the schedule() method, and by the finish()
        method, when a job finishes, so that the maximum number of jobs never
        exceeds `maxjobs`.
        
        """
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
            mutex = job.key.page.mutex()
            if mutex is None or not any(mutex is j.key.page.mutex() for j in runningjobs):
                runningjobs.append(job)
                job.start()

    def finish(self, job):
        """Called by the job when finished.
        
        Puts the image in the cache and checks whether a new job needs to be
        started.
        
        """
        self.cache[job.key] = job.image
        for cb in job.callbacks:
            cb(job.key.page)
        del _jobs[self][job.key.page]
        if not _jobs[self]:
            del _jobs[self]
        else:
            self.checkstart()

