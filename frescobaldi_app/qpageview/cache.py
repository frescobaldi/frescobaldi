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
Cache logic.
"""

import weakref
import time


class ImageEntry:
    def __init__(self, image):
        self.image = image
        self.bcount = image.byteCount()
        self.time = time.time()


class ImageCache:
    """Cache generated images.

    Store and retrieve them under a key (see render.Renderer.key()).


    """
    maxsize = 104857600 # 100M
    currentsize = 0

    def __init__(self):
        self._cache = weakref.WeakKeyDictionary()

    def clear(self):
        """Remove all cached images."""
        self._cache.clear()

    def __getitem__(self, key):
        """Retrieve the exact image.

        Raises a KeyError when there is no cached image for the key.

        """
        return self._cache[key.group][key.page][key.size].image

    def __setitem__(self, key, image):
        """Store the image.

        Automatically removes the oldest cached images to keep the cache
        under maxsize.

        """
        try:
            self.currentsize -= self._cache[key.group][key.page][key.size].bcount
        except KeyError:
            pass

        purgeneeded = self.currentsize > self.maxsize

        e = ImageEntry(image)
        self.currentsize += e.bcount

        self._cache.setdefault(key.group, {}).setdefault(key.page, {})[key.size] = e

        if not purgeneeded:
            return

        # purge old images if needed,
        # cache groups may have disappeared so count all images
        items = []
        items.extend(sorted(
            (entry.time, entry.bcount, group, page, size)
            for group, groupd in self._cache.items()
                for page, paged in groupd.items()
                    for size, entry in sorted(paged.items())[1:]))
        # smallest for each page last
        items.extend(sorted(
            (entry.time, entry.bcount, group, page, size)
            for group, groupd in self._cache.items()
                for page, paged in groupd.items()
                    for size, entry in sorted(paged.items())[:1]))

        # now count the newest images until maxsize ...
        items = reversed(items)
        currentsize = 0
        for time, bcount, group, page, size in items:
            currentsize += bcount
            if currentsize > self.maxsize:
                break
        self.currentsize = currentsize
        # ... and delete the remaining images, deleting empty dicts as well
        for time, bcount, group, page, size in items:
            del self._cache[group][page][size]
            if not self._cache[group][page]:
                del self._cache[group][page]
                if not self._cache[group]:
                    del self._cache[group]

    def closest(self, key):
        """Retrieve the correct image but with a different size.

        This can be used for interim display while the real image is being
        rendered.

        """
        try:
            entries = self._cache[key.group][key.page]
        except KeyError:
            return
        # find the closest size (assuming aspect ratio has not changed)
        if entries:
            width = key.size[0]
            sizes = sorted(entries, key=lambda s: abs(1 - s[0] / width))
            return entries[sizes[0]].image

