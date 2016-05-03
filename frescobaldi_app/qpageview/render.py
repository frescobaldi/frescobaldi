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

from PyQt5.QtGui import QImage


class AbstractImageRenderer:
    """Handle rendering and caching of images.
    
    A renderer can be assigned to the renderer attribute of a Page and takes
    care for generating, caching and updating the images needed for display
    of the Page at different sizes.
    
    You can use a renderer for as many Page instances as you like. You can use
    one global renderer in your application or more, depending on how you use
    the qpageview package.
    
    You must inherit from this class and at least implement the
    render_image_for_job() method.
    
    """
    
    class RenderJob:
        def __init__(self, page):
            self.page = page
            self.width = page.width()
            self.height = page.height()
            self.rotation = page.computedRotation()
        
        def cache_key(self):
            return 
    
    def __init__(self):
        pass
    
    def image(self, page):
        """Return the image rendered at the correct size for this Page. 
        
        Returns None if no suitable image is available.
        
        """
        return self.image_for_job(self.job(page))
    
    def interim_image(self, page):
        """Return an image that has the right contents but the wrong size.
        
        It can be used temporarily, awaiting the rendering of the image at the
        correct size. Returns None if no usable image is available.
        
        """
        return self.interim_image_for_job(self.job(page))

    def draw(self, page, callback):
        """Schedules a (re)draw for the page, calling callback when finished."""
        self.redraw_job(self.job(page), callback)
    
    def render_image(self, page):
        """Reimplement this method to render an image for the page.
        
        It is called in a background thread. It should return a QImage object.
        
        """
        return QImage()

    def job(self, page):
        """Return a RenderJob instance for this page."""
        return self.RenderJob(page)

    def image_for_job(self, job):
        """Return the image that the render job would create."""
        return self.cache.get(job.cache_key())
    
    def interim_image_for_job(self, job):
        """Return an image that has the right contents but the wrong size.
        
        The closest sized image is taken from the cache if available.
        
        """
        return self.cache.get_interim(job.cache_key())
    
    def draw_job(self, job, callback):
        """Schedule a draw job, calls callback when the job is done."""
        
    
