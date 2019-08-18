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
SidebarView, a special View with miniatures to use as a sidebar for a View.

Automatically displays all pages in a view in small size, and makes it easier
to browse large documents.

"""

from . import constants
from . import layout
from . import pagedview
from . import view



class SidebarView(pagedview.PagedViewMixin, view.View):
    """A special View with miniatures to use as a sidebar for a View.

    Automatically displays all pages in a view in small size, and makes it
    easier to browse large documents. Use connectView() to connect a View, and
    it automatically shows the pages, also when the view is changed.
    
    """
    
    MAX_ZOOM = 1.0
    pagingOnScrollEnabled = False
    wheelZoomingEnabled = False
    
    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._view = None
        self.setPageLayout(layout.PageLayout())
        self.setViewMode(constants.FitWidth)
    
    def connectView(self, view):
        """Connects to a view, connecting some signals. """
        if self._view is view:
            return
        if self._view:
            self.disconnectView()
        self._view = view
        if view:
            self.currentPageChanged.connect(view.setCurrentPageNumber)
            view.pageLayoutUpdated.connect(self.slotLayoutUpdated)
            self.slotLayoutUpdated()

    def disconnectView(self):
        """Disconnects the current view."""
        if self._view is not None:
            self.currentPageChanged.disconnect(view.setCurrentPageNumber)
            self._view.pageLayoutUpdated.disconnect(self.slotLayoutUpdated)
    
    def slotLayoutUpdated(self):
        """Called when the layout of the connected view is updated."""
        self.pageLayout()[:] = (p.copy() for p in self._view.pageLayout())
        self.updatePageLayout()

