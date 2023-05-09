# -*- coding: utf-8 -*-
#
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
import sys
import time

from PyQt5.QtCore import QRect, QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QRegion, QTransform

from . import backgroundjob
from . import cache
from . import util

#: Describes a tile to render. Most times all coordinates are integers.
#: The needed tiles for a page are yielded by :meth:`AbstractRenderer.tiles`.
Tile = collections.namedtuple('Tile', 'x y w h')
Tile.x.__doc__ = "The x coordinate of the tile"
Tile.y.__doc__ = "The y coordinate of the tile"
Tile.w.__doc__ = "The width of the tile"
Tile.h.__doc__ = "The height of the tile"

#: Identifies a render operation for a Page, returned by
#: :meth:`AbstractRenderer.key`.
Key = collections.namedtuple("Key", "group ident rotation width height")
Key.group.__doc__ = "The :meth:`~.page.AbstractPage.group` of the page"
Key.ident.__doc__ = "The :meth:`~.page.AbstractPage.ident` of the page"
Key.rotation.__doc__ = "The :attr:`~.page.AbstractPage.computedRotation` of the page"
Key.width.__doc__ = "The :attr:`~.util.Rectangular.width` of the page"
Key.height.__doc__ = "The :attr:`~.util.Rectangular.height` of the page"

#: Information about cached or missing rendered tiles to display a rectangular
#: part of a Page at a certain size. Returned by :meth:`AbstractRenderer.info`.
RenderInfo = collections.namedtuple("RenderInfo", "images missing key target ratio")
RenderInfo.images.__doc__ = "a list of tuples (tile, image) that are available in the cache"
RenderInfo.missing.__doc__ = "a list of Tile instances that are needed but not available in the cache"
RenderInfo.key.__doc__ = "the Key returned by :meth:`~AbstractRenderer.key`, describing width, height, rotation and identity of the page"
RenderInfo.target.__doc__ = "the rect multiplied by the ratio"
RenderInfo.images.__doc__ = "the devicepixelratio of the specified paint device"

# the maximum number of concurrent jobs (at global level)
maxjobs = 4

# we use a global dict to keep running jobs in, so a thread is never
# deallocated when a renderer dies.
_jobs = {}



class AbstractRenderer:
    """Handle rendering and caching of images.

    A renderer can be assigned to the renderer attribute of a Page and takes
    care for generating, caching and updating the images needed for display
    of the Page at different sizes.

    You can use a renderer for as many Page instances as you like. You can use
    one global renderer in your application or more, depending on how you use
    the qpageview package.

    You must inherit from this class and at least implement the render() or the
    draw() method.

    Instance attributes:

    ``paperColor``
        Paper color. If possible this background color is used when rendering
        the pages, also for temporary drawings when a page has to be rendered.
        If a Page specifies its own paperColor, that color prevails.

    ``imageFormat``
        QImage format to use (if possible). Default is
        QImage.Format_ARGB32_Premultiplied

    ``antialiasing``
        True by default. Whether to antialias graphics. (Most Renderers
        antialias anyway, even if this is False.)

    """

    MAX_TILE_WIDTH = 2400
    MAX_TILE_HEIGHT = 1600

    # default paper color to use (if possible, and when drawing an empty page)
    paperColor = QColor(Qt.white)

    # QImage format to use (if possible)
    imageFormat = QImage.Format_ARGB32_Premultiplied

    # antialias True by default (not all renderers may support this)
    antialiasing = True

    def __init__(self, cache=None):
        if cache:
            self.cache = cache

    def copy(self):
        """Return a copy of the renderer, with always a new cache."""
        c = self.cache
        if c:
            c = type(c)()
            c.__dict__.update(self.cache.__dict__)
        r = type(self)(c)
        r.__dict__.update(self.__dict__)
        return r

    @staticmethod
    def key(page, ratio):
        """Return a five-tuple Key describing the page.

        The ratio is a device pixel ratio; width and height are multiplied
        with this value, to render and cache an image correctly on high-
        density displays.

        This is used for rendering and caching. It is never stored as is.
        The cache can store the group object using a weak reference.
        The tuple contains the following values:

        ``group``
            the object returned by ``page.group()``
        ``ident``
            the value returned by ``page.ident()``
        ``rotation``
            ``page.computedRotation``
        ``width``
            ``page.width * ratio``
        ``height``
            ``page.height * ratio``

        """
        return Key(
            page.group(),
            page.ident(),
            page.computedRotation,
            int(page.width * ratio),
            int(page.height * ratio),
        )

    def tiles(self, width, height):
        """Yield four-tuples Tile(x, y, w, h) describing the tiles to render."""
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
                yield Tile(x, y, w, h)
                x += w
            y += h

    def map(self, key, box):
        """Return a QTransform converting from Key coordinates to a box.

        The box should be a QRectF or QRect, and describes the original area of
        the page.  The returned matrix can be used to convert e.g. tile
        coordinates to the position on the original page.

        """
        t = QTransform()
        t.translate(box.x(), box.y())
        t.scale(box.width(), box.height())
        t.translate(.5, .5)
        t.rotate(-key.rotation * 90)
        t.translate(-.5, -.5)
        t.scale(1 / key.width, 1 / key.height)
        return t

    def image(self, page, rect, dpiX, dpiY, paperColor):
        """Returns a QImage of the specified rectangle on the Page.

        The rectangle is relative to the top-left position. The image is not
        cached.

        """
        s = page.defaultSize()
        hscale = s.width() * dpiX / page.dpi / page.width
        vscale = s.height() * dpiY / page.dpi / page.height
        matrix = QTransform().scale(hscale, vscale)

        tile = Tile(*matrix.mapRect(rect).getRect())
        key = Key(page.group(),
                  page.ident(),
                  page.computedRotation,
                 *matrix.map(page.width, page.height))
        return self.render(page, key, tile, paperColor)

    def render(self, page, key, tile, paperColor=None):
        """Generate a QImage for tile of the Page.

        The width, height and rotation to render at should be taken from the
        key, as the page could be resized or rotated in the mean time.

        The default implementation prepares the image, a painter and then
        calls draw() to actually draw the contents.

        If the paperColor is not specified, it will be read from the Page's
        paperColor attribute (if not None) or else from the renderer's
        paperColor attribute.

        """
        if paperColor is None:
            paperColor = page.paperColor or self.paperColor

        i = QImage(tile.w, tile.h, self.imageFormat)
        i.fill(paperColor)
        painter = QPainter(i)

        # rotate the painter accordingly
        util.rotate(painter, key.rotation, tile.w, tile.h, True)

        # draw it on the image
        self.draw(page, painter, key, tile, paperColor)
        return i

    def draw(self, page, painter, key, tile, paperColor=None):
        """Draw the page contents; implement at least this method.

        The painter is already at the top-left position and the correct
        rotation. You should convert the tile to the original area on the page,
        you can use the map() method for that. You can draw in tile/key
        coordinates. Don't use width, height and rotation from the Page object,
        as it could have been resized or rotated in the mean time.

        The paperColor can be speficied, but it is not needed to paint it: by
        default the render() method already fills the image, and when drawing on
        a printer, painting the background is normally not desired.

        """
        pass

    def info(self, page, device, rect):
        """Return a namedtuple RenderInfo(images, missing, key, target, ratio).

        images is a list of tuples (tile, image) that are available in the
        cache; missing is a list of Tile instances that are not available in
        the cache; key is the Key returned by key(), describing width, height,
        rotation and identity of the page; target is the rect multiplied by the
        ratio; which is the devicepixelratio of the specified paint device.

        """
        try:
            ratio = device.devicePixelRatioF()
        except AttributeError:
            ratio = device.devicePixelRatio()
        key = self.key(page, ratio)

        # paint rect in tile coordinates
        target = QRect(int(rect.x() * ratio), int(rect.y() * ratio), int(rect.width() * ratio), int(rect.height() * ratio))

        # tiles to paint
        tiles = [t for t in self.tiles(key.width, key.height) if QRect(*t) & target]

        # look in cache, get a dict with tiles and their images
        tileset = self.cache.tileset(key)

        images = []
        missing = []
        for t in tiles:
            entry = tileset.get(t)
            if entry:
                entry.time = time.time()    # prevent aging ;-)
                images.append((t, entry.image))
            else:
                missing.append(t)

        return RenderInfo(images, missing, key, target, ratio)

    def update(self, page, device, rect, callback=None):
        """Check if a page can be painted on the device without waiting.

        Return True if that is the case. Otherwise schedules missing tiles
        for rendering and calls the callback each time one tile if finished.

        """
        info = self.info(page, device, rect)
        if info.missing:
            self.schedule(page, info.key, info.missing, callback)
            return False
        return True

    def paint(self, page, painter, rect, callback=None):
        """Paint a page, using images from the cache.

        ``page``:
            the Page to draw

        ``painter``:
            the QPainter to use to draw

        ``rect``:
            the region to draw, relative to the topleft of the page.

        ``callback``:
            if specified, a callable accepting the `page` argument.
            Typically this should be used to trigger a repaint of the view.

        The Page calls this method by default in its
        :meth:`~.page.AbstractPage.paint` method. This method tries to fetch an
        image from the cache and paint that. If no image is available, render()
        is called in the background to generate one. If it is ready, the
        callback is called with the Page as argument. An interim image may be
        painted in the meantime (e.g. scaled from another size).

        """
        images = [] # list of images to draw at end of this method
        region = QRegion() # painted region in tile coordinates

        info = self.info(page, painter.device(), rect)

        for t, image in info.images:
            r = QRect(*t) & info.target # part of the tile that needs to be drawn
            images.append((r, image,  QRectF(r.translated(-t.x, -t.y))))
            region += r

        if info.missing:
            self.schedule(page, info.key, info.missing, callback)

            # find other images from cache for missing tiles
            for width, height, tileset in self.cache.closest(info.key):
                # we have a dict of tiles for an image of size width x height
                hscale = info.key.width / width
                vscale = info.key.height / height
                for t in tileset:
                    # scale to our image size
                    r = QRect(int(t.x * hscale), int(t.y * vscale), int(t.w * hscale), int(t.h * vscale)) & info.target
                    if r and QRegion(r).subtracted(region):
                        # we have an image that can be drawn in rect r
                        source = QRectF(r.x() / hscale - t.x, r.y() / vscale - t.y,
                                        r.width() / hscale, r.height() / vscale)
                        images.append((r, tileset[t].image, source))
                        region += r
                        # stop if we have covered the whole drawing area
                        if not QRegion(info.target).subtracted(region):
                            break
                else:
                    continue
                break
            else:
                if QRegion(info.target).subtracted(region):
                    # paint background, still partly uncovered
                    painter.fillRect(rect, page.paperColor or self.paperColor)

        # draw lowest quality images first
        for (r, image, source) in reversed(images):
            # scale the target rect back to the paint device
            target = QRectF(r.x() / info.ratio, r.y() / info.ratio, r.width() / info.ratio, r.height() / info.ratio)
            painter.drawImage(target, image, source)

    def schedule(self, page, key, tiles, callback):
        """Schedule a new rendering job for the specified tiles of the page.

        If this page has already a job pending, the callback is added to the
        pending job.

        """
        for tile in tiles:
            try:
                job = _jobs[(key, tile)]
            except KeyError:
                # make a new Job for this tile
                job = _jobs[(key, tile)] = self.job(page, key, tile)
            job.time = time.time()
            job.callbacks.add(callback)
        self.checkstart()

    def job(self, page, key, tile):
        """Return a new :class:`~.backgroundjob.Job` tailored for this tile."""
        job = backgroundjob.Job()
        job.callbacks = callbacks = set()
        job.mutex = page.mutex()
        exception = []
        def work():
            try:
                return self.render(page, key, tile)
            except Exception:
                exception.extend(sys.exc_info())
                return QImage()
        def finalize(image):
            self.cache.addtile(key, tile, image)
            for cb in callbacks:
                cb(page)
            del _jobs[(key, tile)]
            self.checkstart()
            if exception:
                self.exception(*exception)
        job.work = work
        job.finalize = finalize
        return job

    def unschedule(self, pages, callback):
        """Unschedule a possible pending rendering job for the given pages.

        If the pending job has no other callbacks left, it is removed,
        unless it is running.

        """
        pages = set((p.group(), p.ident()) for p in pages)
        unschedule = []
        for (key, tile), job in _jobs.items():
            if key[:2] in pages:
                job.callbacks.discard(callback)
                if not job.callbacks and not job.running:
                    unschedule.append((key, tile))
        for jobkey in unschedule:
            job = _jobs.pop(jobkey)
            job.finalize = job.work = None

    def invalidate(self, pages):
        """Delete the cached images for the given pages."""
        for p in pages:
            self.cache.invalidate(p)

    def checkstart(self):
        """Check whether there are jobs that need to be started.

        This method is called by the schedule() method, and by the finish()
        method when a job finishes, so that the number of running jobs never
        exceeds `maxjobs`.

        """
        runningjobs = [job for job in _jobs.values() if job.running]
        waitingjobs = sorted((job for job in _jobs.values() if not job.running),
                        key=lambda j: j.time, reverse=True)     # newest first

        jobcount = maxjobs - len(runningjobs)
        if jobcount > 0:
            mutexes = set(j.mutex for j in runningjobs)
            mutexes.discard(None)
            for job in waitingjobs:
                m = job.mutex
                if m is None or m not in mutexes:
                    mutexes.add(m)
                    job.start()
                    jobcount -= 1
                    if jobcount == 0:
                        break

    def exception(self, exctype, excvalue, exctb):
        """Called when an exception has occurred in a background rendering job.

        The default implementation prints a traceback to stderr.

        """
        import traceback
        traceback.print_exception(exctype, excvalue, exctb)



# install a global cache to use by default
AbstractRenderer.cache = cache.ImageCache()


