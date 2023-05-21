# -*- coding: utf-8 -*-
#
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
ImageView, a View optimized for display of one Page, e.g. one image.

Clicking in the view toggles between FitBoth and NaturalSize.

"""


from PyQt5.QtCore import QMargins, Qt

from . import constants
from . import util
from . import view


class ImageViewMixin:
    """View Mixin with a few customisations for displaying a single page/image.

    Adds the instance variable:

        fitNaturalSizeEnabled = True

                If True, the image will not be scaled larger than its natural
                size when FitWidth, -Height, or -Both is active.

    """
    fitNaturalSizeEnabled = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(constants.FitBoth)
        self.pageLayout().setMargins(QMargins(0, 0, 0, 0))

    def setImage(self, image):
        """Convenience method to display a QImage."""
        self.loadImages([image])

    def toggleZooming(self):
        """Toggles between FitBoth and natural size."""
        if self.viewMode() == constants.FitBoth:
            self.setViewMode(constants.FixedScale)
            self.zoomNaturalSize()
        else:
            self.setViewMode(constants.FitBoth)

    def fitPageLayout(self):
        """Reimplemented to avoid zooming-to-fit larger than naturalsize."""
        layout = self.pageLayout()
        if self.fitNaturalSizeEnabled and self.viewMode() and layout.count():
            zoom_factor = layout.zoomFactor
            # fit layout but prevent zoomFactorChanged from being emitted
            with util.signalsBlocked(self):
                super().fitPageLayout()
            # what would be the natural size?
            factor = layout[0].dpi / self.physicalDpiX()
            # adjust if the image was scaled larger
            if layout.zoomFactor > factor:
                layout.zoomFactor = factor
            if zoom_factor != layout.zoomFactor:
                self.zoomFactorChanged.emit(layout.zoomFactor)
        else:
            super().fitPageLayout()

    def mouseReleaseEvent(self, ev):
        """Reimplemented to toggle between FitBoth and ZoomNaturalSize."""
        if not self.isDragging() and ev.button() == Qt.LeftButton:
            self.toggleZooming()
        super().mouseReleaseEvent(ev)


class ImageView(ImageViewMixin, view.View):
    """A View, optimized for display of one Page, e.g. one image.

    Append one Page to the layout, use one of the load* methods to load
    a single page document, or use the setImage() method to display a QImage.

    """
    clickToSetCurrentPageEnabled = False


