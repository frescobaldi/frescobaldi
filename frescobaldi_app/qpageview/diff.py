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
A Page intended to display the visual difference between other pages.

"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap

from . import multipage


class DiffPage(multipage.MultiPage):
    """A Page that shows the difference between sub pages.

    DiffPage inherits from MultiPage; the pages are to be added in the pages
    attribute. The first page is considered to be the "default" page, shown
    the normal way; the others are added in configurable colors and intensity.
    
    """
    opaquePages = False


class DiffRenderer(multipage.MultiPageRenderer):
    """Renders the pages by calling their own renderer.
    
    How the difference is displayed can be configured using this renderer.
    Up to four different pages can be displayed, the colors to render them
    are taken from the colors instance variable, which is a list.
    
    The alpha channel of each color determines the visiblity of the 
    corresponding sub page.
    
    This renderer works best with pages that are mostly black on a white
    background.
    
    """
    def __init__(self):
        # we don't use a cache so no need to call super init
        self.colors = [
            QColor(Qt.black),
            QColor(Qt.red),
            QColor(Qt.green),
            QColor(Qt.blue),
        ]
    
    def combine(self, painter, images):
        """Paint images on the painter.

        Each image is a tuple(QPoint, QPixmap), describing where to draw.
        The image on top is first, so drawing should start with the last.

        """
        for color, (pos, image) in zip(self.colors, images):
            # take the alpha component
            intensity = 255 - color.alpha()
            if intensity == 255:
                continue    # the image would appear white anyway
            color = color.rgb()
            color |= 0x010101 * intensity
            color |= 0xFF000000
            
            p = QPainter(image)
            p.setCompositionMode(QPainter.CompositionMode_Lighten)
            p.fillRect(image.rect(), QColor(color))
            p.end()
            if isinstance(image, QPixmap):
                painter.drawPixmap(pos, image)
            else:
                painter.drawImage(pos, image)
            painter.setCompositionMode(QPainter.CompositionMode_Darken)

    def print(self, page, painter, rect, paperColor):
        """Print the sub pages at the correct position."""
        painter.save()
        painter.translate(-rect.topLeft())
        # print from bottom to top
        for layer, (p, m) in enumerate(reversed(list(page.printablePagesAt(rect)))):
            # find center of the page corresponding to our center
            painter.save()
            ### TODO implement diff like combine()
            painter.setTransform(m, True)
            # handle rect clipping
            clip = m.inverted()[0].mapRect(rect) & p.pageRect()
            painter.fillRect(clip, paperColor or Qt.white)    # draw a white background
            painter.translate(clip.topLeft())   # the page will go back...
            p.print(painter, clip)
            painter.restore()
        painter.restore()



# install a default renderer, so DiffPage can be used directly
DiffPage.renderer = DiffRenderer()



