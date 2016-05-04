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


cache_key = collections.namedtuple('cache_key', 'group page rotation size')


class Request:
    """Describes a request to render a Page.
    
    You can instantiate a Request and use it directly, but you can also alter 
    the `rotation` attribute and/of use the recomputeSize() method to change 
    the size of the to be rendered image.
    
    """
    def __init__(self, page):
        self.page = page
        self.rotation = page.computedRotation
        self.width = page.width
        self.height = page.height
    
    def recomputeSize(self, dpiX=72.0, dpiY=None, zoomFactor=1.0):
        """Re-compute our width and height, using Page.computeSize().
        
        You can use this to base a request on a Page but alter e.g. the 
        zoom. dpiX defaults to 72.0 and dpiY defaults to dpiX
        
        """
        if dpiY is None:
            dpiY = dpiX
        self.width, self.height = self.page.computeSize(
            self.rotation, dpiX, dpiY, zoomFactor)



class AbstractImageRenderer:
    """Handle rendering and caching of images.
    
    A renderer can be assigned to the renderer attribute of a Page and takes
    care for generating, caching and updating the images needed for display
    of the Page at different sizes.
    
    You can use a renderer for as many Page instances as you like. You can use
    one global renderer in your application or more, depending on how you use
    the qpageview package.

    When rendering the image for a Page, a Request is created which can be
    scheduled or rendered directly. You can also schedule requests for a page
    at different sizes.
    
    You must inherit from this class and at least implement the
    render() method.
    
    """
    def __init__(self):
        pass
    
    def request(self, page):
        """Return a Request for the Page."""
        return Request(page)
    
    def key(self, request):
        """Return a cache_key instance for this request.
        
        The cache_key is a four-tuple:
        
            group       = an object a weak reference is taken to. It could be
                          a document or some other structure the page belongs to.
                          by default the Page object attached to the request is
                          used.

            page        = None by default, but if you use group differently,
                          you should use here a hashable object that identifies
                          the page in the group.
                          
            rotation    = the rotation of the page
            
            size        = the (width, height) tuple of the page.
        
        The cache_key is used to store requests and to cache results.
        
        """
        return cache_key(
            request.page,
            None,
            request.rotation,
            (request.width, request.width))

    def render(self, request):
        """Reimplement this method to generate an image for this request."""


