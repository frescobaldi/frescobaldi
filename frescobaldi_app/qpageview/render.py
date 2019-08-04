# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
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

from PyQt5.QtCore import QRect, QRectF, Qt, QThread
from PyQt5.QtGui import QColor, QImage, QRegion

from . import cache


tile = collections.namedtuple('tile', 'x y w h')
key = collections.namedtuple("key", "group ident rotation width height")


# the maximum number of concurrent jobs (at global level)
maxjobs = 4

# we use a global dict to keep running jobs in, so a thread is never
# deallocated when a renderer dies.
_jobs = collections.defaultdict(dict)


class Job(QThread):
    """A simple wrapper around QThread.
    
    Job is instantiated with the Page to render, the Renderer to use, the
    key that describes rotation, width and height, and the tile to render.
    
    You don't need to instantiate Job objects, that is done by the schedule()
    method of AbstractImageRenderer.
    
    """
    def __init__(self, renderer, page, key, tile):
        super().__init__()
        self.renderer = renderer
        self.page = page
        self.key = key
        self.tile = tile
        
        self.image = None
        self.running = False
        self.callbacks = set()
        self.finished.connect(self._slotFinished)

    def start(self):
        self.running = True
        super().start()
    
    def run(self):
        """This is called in the background thread by Qt."""
        self.image = self.renderer.render(self.page, self.key, self.tile)

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
        
        `drawThumbnail` True by default. Whether to draw temporary thumbnail
                        images embedded in the PDF if they are available. The 
                        thumbnail will be visible shortly, because a genuine 
                        image will always be rendered.

    """
    
    MAX_TILE_WIDTH = 2400
    MAX_TILE_HEIGHT = 1600
    
    # default paper color to use (if possible, and when drawing an empty page)
    paperColor = QColor(Qt.white)
    
    # whether to temporarily display embedded thumbnails if they are available
    drawThumbnail = True

    def __init__(self):
        self.cache = cache.ImageCache()
    
    @staticmethod
    def key(page, ratio):
        """Return a five-tuple describing the page.
        
        The ratio is a device pixel ratio; width and height are multiplied
        with this value, to render and cache an image correctly on high-
        density displays.
        
        This is used for rendering and caching. It is never stored as is.
        The cache can store the group object using a weak reference.
        The tuple contains the following values:
        
        group       the object returned by group()
        ident       the value returned by ident()
        rotation    self.computedRotation
        width       self.width * ratio
        height      self.height * ratio
        
        """
        return key(
            page.group(),
            page.ident(),
            page.computedRotation,
            int(page.width * ratio),
            int(page.height * ratio),
        )

    def tiles(self, width, height):
        """Yield four-tuples (x, y, w, h) describing the tiles to render."""
        rowcount = height // self.MAX_TILE_HEIGHT
        colcount = width  // self.MAX_TILE_WIDTH
        tilewidth, extrawidth = divmod(width, colcount + 1)
        tileheight, extraheight = divmod(height, rowcount + 1)
        rows = [tileheight] * rowcount + [tileheight + extraheight]
        cols = [tilewidth] * colcount + [tilewidth + extrawidth]
        y = 0
        for h in rows:
            x = 0
            for w in cols:
                yield tile(x, y, w, h)
                x += w
            y += h

    def render(self, page, key, tile):
        """Reimplement this method to generate a QImage for tile of the Page.
        
        The width, height and rotation to render at should be taken from the
        key, as the page could be resized or rotated in the mean time.
        
        """
        return QImage()
    
    def images(self, key, target):
        """Yields three-tuples (tile, valid, image) for the rect target.
        
        Together the tiles fill the target rect completely. valid is a bool; if 
        true the image was available in the cache, can be drawn and is still 
        uptodate. If false, the tile should be scheduled for re-render; if an 
        image is there it can be drawn in the meantime.
        
        """
        # tiles to paint
        tiles = set(t for t in self.tiles(key.width, key.height) if QRect(*t) & target)
        
        # look in cache, get a dict with tiles and their images
        tileset = self.cache.tileset(key)
        
        for t in tiles:
            entry = tileset.get(t)
            if entry:
                yield t, not entry.replace, entry.image
            else:
                yield t, False, None

    def paint(self, page, painter, rect, callback=None):
        """Paint a page.
        
        page: the Page to draw

        painter:  the QPainter to use to draw
        
        rect: the region to draw, relative to the topleft of the page.
        
        callback: if specified, a callable accepting the `page` argument.
        Typically this should be used to trigger a repaint of the view.
        
        The Page calls this method by default in the paint() method.
        This method tries to fetch an image from the cache and paint that.
        If no image is available, render() is called in the background to
        generate one. If it is ready, the callback is called with the Page
        as argument. An interim image may be painted in the meantime (e.g.
        scaled from another size).

        """
        try:
            ratio = painter.device().devicePixelRatioF()
        except AttributeError:
            ratio = painter.device().devicePixelRatio()
        key = self.key(page, ratio)
        
        # paint rect in tile coordinates
        target = QRect(rect.x() * ratio, rect.y() * ratio, rect.width() * ratio, rect.height() * ratio)
        region = QRegion() # unpainted region in tile coordinates
        images = []
        
        schedule = set()
        for t, valid, image in self.images(key, target):
            if not valid:
                schedule.add(t)
            if image:
                r = QRect(*t) & target # part of the tile that needs to be drawn
                images.append((r, image,  QRectF(r.translated(-t.x, -t.y))))
                region += r
        
        # reschedule images to be generated
        if schedule:
            self.schedule(page, ratio, schedule, callback)
        
        if QRegion(target).subtracted(region):
            # find other images from cache for missing tiles
            for width, height, tileset in self.cache.closest(key):
                # we have a dict of tiles for an image of size width x height
                hscale = key.width / width
                vscale = key.height / height
                for t in tileset:
                    # scale to our image size
                    r = QRect(t.x * hscale, t.y * vscale, t.w * hscale, t.h * vscale) & target
                    if r and QRegion(r).subtracted(region):
                        # we have an image that can be drawn in rect r
                        source = QRectF(r.x() / hscale - t.x, r.y() / vscale - t.y,
                                        r.width() / hscale, r.height() / vscale)
                        images.append((r, tileset[t].image, source))
                        region += r
                        # stop if we have covered the whole drawing area
                        if not QRegion(target).subtracted(region):
                            break
                else:
                    continue
                break
            else:
                if QRegion(target).subtracted(region):
                    # paint background, still partly uncovered
                    color = page.paperColor or self.paperColor or QColor(Qt.white)
                    painter.fillRect(rect, color)
                    
                    if self.drawThumbnail:
                        # draw thumbnail if available
                        thumb = page.thumbnail()
                        if thumb and not thumb.isNull():
                            hscale = key.width / thumb.width()
                            vscale = key.height / thumb.height()
                            source = QRectF(target.x() / hscale, target.y() / vscale,
                                            target.width() / hscale, target.height() / vscale)
                            images.append((target, image, source))
        
        # draw lowest quality images first
        for (r, image, source) in reversed(images):
            # scale the target rect back to the paint device
            target = QRectF(r.x() / ratio, r.y() / ratio, r.width() / ratio, r.height() / ratio)
            painter.drawImage(target, image, source)

    def schedule(self, page, ratio, tiles, callback):
        """Schedule a new rendering job for the specified tiles of the page.
        
        If this page has already a job pending, the callback is added to the
        pending job.
        
        """
        key = self.key(page, ratio)
        tiled = _jobs[self].setdefault(page, {}).setdefault(key, {})
        
        for tile in tiles:
            try:
                job = tiled[tile]
            except KeyError:
                job = tiled[tile] = Job(self, page, key, tile)
            job.time = time.time()
            job.callbacks.add(callback)
        self.checkstart()

    def unschedule(self, pages, callback):
        """Unschedule a possible pending rendering job for the given pages.

        If the pending job has no other callbacks left, it is removed,
        unless it is running.

        """
        for p in pages:
            d = _jobs[self].get(p)
            if d:
                jobs = [(key, tile, job)
                    for key, tiled in d.items()
                        for tile, job in tiled.items()]
                for key, tile, job in jobs:
                    job.callbacks.discard(callback)
                    if not job.callbacks and not job.running:
                        del d[key][tile]
                        if not d[key]:
                            del d[key]
                if not d:
                    del _jobs[self][p]
        if not _jobs[self]:
            del _jobs[self]

    def checkstart(self):
        """Check whether there are jobs that need to be started.
        
        This method is called by the schedule() method, and by the finish()
        method, when a job finishes, so that the maximum number of jobs never
        exceeds `maxjobs`.
        
        """
        runningjobs = [job
            for page, keys in _jobs[self].items()
                for key, tiled in keys.items()
                    for tile, job in tiled.items()
                        if job.running]
        waitingjobs = sorted((job
            for page, keys in _jobs[self].items()
                for key, tiled in keys.items()
                    for tile, job in tiled.items()
                        if not job.running),
                            key=lambda j: j.time, reverse=True)
        jobcount = len(runningjobs)
        for job in waitingjobs[:maxjobs-jobcount]:
            mutex = job.page.mutex()
            if mutex is None or not any(mutex is j.page.mutex() for j in runningjobs):
                runningjobs.append(job)
                job.start()

    def finish(self, job):
        """Called by the job when finished.
        
        Puts the image in the cache and checks whether a new job needs to be
        started.
        
        """
        self.cache.addtile(job.key, job.tile, job.image)
        for cb in job.callbacks:
            cb(job.page)

        del _jobs[self][job.page][job.key][job.tile]
        if not _jobs[self][job.page][job.key]:
            del _jobs[self][job.page][job.key]
            if not _jobs[self][job.page]:
                del _jobs[self][job.page]
        if not _jobs[self]:
            del _jobs[self]
        else:
            self.checkstart()



