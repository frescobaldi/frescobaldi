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

from PyQt5.QtGui import QPixmap

from . import multipage


class CompositePage(multipage.MultiPage):
    """A Page that can draw multiple pages over each other.

    CompositePage inherits from MultiPage, but composites the pages
    on top of each other in a configurable way.
    
    """
    opaquePages = False


class CompositeRenderer(multipage.MultiPageRenderer):
    """Composite the pages by calling their own renderer."""
    opacity = [1, 0.5, 0.5]
    
    def combine(self, painter, images):
        """Paint images on the painter.

        Each image is a tuple(QPoint, QPixmap), describing where to draw.
        The image on top is first, so drawing should start with the last.

        """
        ### TODO: move compositing to a specific class and add much
        ### more options
        for layer, (pos, image) in enumerate(reversed(images)):
            painter.setOpacity(self.opacity[layer])
            if isinstance(image, QPixmap):
                painter.drawPixmap(pos, image)
            else:
                painter.drawImage(pos, image)



# install a default renderer, so CompositePage can be used directly
CompositePage.renderer = CompositeRenderer()



