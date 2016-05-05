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

from PyQt5.QtGui import QImage

from . import cache


cache_key = collections.namedtuple('cache_key', 'group page size')


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
        # TEMP
        key = self.key(page)
        try:
            image = self.cache[key]
        except KeyError:
            image = self.render(page)
            self.cache[key] = image
        painter.drawImage(rect, image, rect)

