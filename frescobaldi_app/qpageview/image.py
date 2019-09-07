# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
A page that can display a QImage,
without using a renderer.

"""


from . import page


class ImagePage(page.AbstractPage):
    dpi = 96   # TODO: maybe this can be image dependent.
    
    def __init__(self, image):
        super().__init__()
        self._image = image
        self.setPageSize(image.size())
        
    def paint(self, painter, rect, callback=None):
        """Paint our image in the View."""
        source = self.mapFromPage().rect()
        

    def print(self, painter, rect=None, paperColor=None):
        """Paint a page for printing."""

    def image(self, rect=None, dpiX=None, dpiY=None, paperColor=None):
        """Returns a QImage of the specified rectangle.

