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
import weakref
import time

from PyQt5.QtCore import QRectF, Qt, QThread
from PyQt5.QtGui import QColor, QImage

from . import cache


cache_key = collections.namedtuple('cache_key', 'group page size')


class Job(QThread):
    def __init__(self, renderer, page):
        super().__init__()
        self.renderer = renderer
        self.page = page
        self.page_copy = page.copy()
        self.image = None
        self.time = time.time()
        self.finished.connect(self._slotFinished)
        self.callbacks = set()
        
    def run(self):
        self.key = self.renderer.key(self.page_copy)
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
    
    """
    def __init__(self):
        self.cache = cache.ImageCache()
        self._jobs = {}
    
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
        as argument. An interim image may be painted in the mean time (e.g.
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
                painter.fillRect(rect, QColor(Qt.white))
            self.schedule(page, painter, callback)
        else:
            painter.drawImage(rect, image, rect)

    
    def schedule(self, page, painter, callback):
        """Start a new rendering job."""
        try:
            job = self._jobs[page]
        except KeyError:
            job = self._jobs[page] = Job(self, page)
            job.start()
        job.callbacks.add(callback)    
        
    def finish(self, job):
        """Called by the job when finished."""
        self.cache[job.key] = job.image
        for cb in job.callbacks:
            cb(job.page)
        del self._jobs[job.page]

