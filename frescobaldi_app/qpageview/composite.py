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
A Page with composite capabilities: to paint multiple pages over each other.

The Renderer acts as a composition manager; settings about how to combine
the pages are done in the renderer.

"""


from . import page
from . import render



class CompositePage(page.AbstractPage):
    """A Page that can draw multiple pages over each other.
    
    The pages to be drawn are in the pages attribute.
    
    """
    def __init__(self, pages=None, renderer=None):
        super().__init__()
        self.pages = pages if pages is not None else []
        self.pageWidth = max(p.pageWidth for p in self.pages)
        self.pageHeight = max(p.pageHeight for p in self.pages)
        if renderer is not None:
            self.renderer = renderer


class Renderer(render.AbstractImageRenderer):
    """Paints the pages by calling their own renderer."""
    
    def __init__(self):
        super().__init__()
        self.opacity = [1.0, 0.5]
    
    def paint(self, page, painter, rect, callback=None):
        props = page.x, page.y, page.height, page.width, page.computedRotation
        for layer, p in enumerate(page.pages):
            p.x, p.y, p.height, p.width, p.computedRotation = props
            painter.setOpacity(self.opacity[layer])
            p.paint(painter, rect, callback)


