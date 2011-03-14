# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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
View widget to display PDF documents.
"""


from PyQt4.QtCore import QPoint, QTimer, Qt, pyqtSignal
from PyQt4.QtGui import QPalette, QScrollArea

import popplerqt4

from . import surface
from . import cache

from . import (
    # viewModes:
    FixedScale,
    FitWidth,
    FitHeight,
    FitBoth,
)


# most used keyboard modifiers
_SCAM = (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META)


class View(QScrollArea):
    
    viewModeChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        
        self.setAlignment(Qt.AlignCenter)
        self.setBackgroundRole(QPalette.Dark)

        self._viewMode = FixedScale
        self._wheelZoomEnabled = True
        self._wheelZoomModifier = Qt.CTRL
        
        # delayed resize
        self._resizeTimer = QTimer(singleShot = True, timeout = self._resizeTimeout)
        self._oldsize = None
        
    def surface(self):
        """Returns our Surface, the widget drawing the page(s)."""
        sf = self.widget()
        if not sf:
            sf = surface.Surface(self)
            self.setSurface(sf)
        return sf
    
    def setSurface(self, sf):
        """Sets the given surface as our widget."""
        self.setWidget(sf)
    
    def viewMode(self):
        """Returns the current ViewMode."""
        return self._viewMode
        
    def setViewMode(self, mode):
        """Sets the current ViewMode."""
        if mode == self._viewMode:
            return
        self._viewMode = mode
        if mode:
            # change view
            self.surface().pageLayout().fit(self.viewport().size(), mode)
            self.surface().pageLayout().update()
        self.viewModeChanged.emit(mode)
    
    def wheelZoomEnabled(self):
        """Returns whether wheel zoom is enabled."""
        return self._wheelZoomEnabled
        
    def setWheelZoomEnabled(self, enabled):
        """Sets whether wheel zoom is enabled.
        
        Wheel zoom is zooming using the mouse wheel and a keyboard modifier key
        (defaulting to Qt.CTRL).  Use setWheelZoomModifier() to set a key (or
        key combination).
        
        """
        self._wheelZoomEnabled = enabled
    
    def wheelZoomModifier(self):
        """Returns the modifier key to wheel-zoom with (defaults to Qt.CTRL)."""
        return self._wheelZoomModifier
        
    def setWheelZoomModifier(self, key):
        """Sets the modifier key to wheel-zoom with (defaults to Qt.CTRL).
        
        Can also be set to a ORed value, e.g. Qt.SHIFT|Qt.ALT.
        Only use Qt.ALT, Qt.CTRL, Qt.SHIFT and/or Qt.META.
        
        """
        self._wheelZoomModifier = key
        
    def load(self, document):
        """Convenience method to load all the pages from the given Poppler.Document."""
        self.surface().pageLayout().load(document)
        if self.viewMode():
            self.surface().pageLayout().fit(self.viewport().size(), self.viewMode())
        self.surface().pageLayout().update()

    def clear(self):
        """Convenience method to clear the current layout."""
        self.surface().pageLayout().clear()
        self.surface().pageLayout().update()

    def scale(self):
        """Returns the scale of the pages in the View."""
        return self.surface().pageLayout().scale()
        
    def setScale(self, scale):
        """Sets the scale of all pages in the View."""
        self.surface().pageLayout().setScale(scale)
        self.surface().pageLayout().update()
        self.setViewMode(FixedScale)

    def visiblePages(self):
        """Yields the visible pages."""
        rect = self.viewport().rect()
        rect.translate(-self.surface().pos())
        rect.intersect(self.surface().rect())
        return self.surface().pageLayout().pagesAt(rect)

    def redraw(self):
        """Redraws, e.g. when you changed rendering hints or papercolor on the document."""
        pages = list(self.visiblePages())
        documents = set(page.document() for page in pages)
        for document in documents:
            cache.clear(document)
        for page in pages:
            cache.generate(page)

    def resizeEvent(self, ev):
        super(View, self).resizeEvent(ev)
        # Detect a resize loop due to scrollbar disappearing
        if self.viewMode() and any(self.surface().pageLayout().pages()):
            diff = ev.size() - ev.oldSize()
            if self.size() == self._oldsize and (
                (diff.width() > 0 and self.viewMode() & FitWidth)
                or (diff.height() > 0 and self.viewMode() & FitHeight)):
                pass # avoid a loop
            else:
                if not self._resizeTimer.isActive():
                    # store the point currently in the center
                    self._centerPos = QPoint(self.width(), self.height()) / 2 - self.surface().pos()
                self._resizeTimer.start(100)
        self._oldsize = self.size()
    
    def _resizeTimeout(self):
        x = self._centerPos.x() / float(self.surface().width())
        y = self._centerPos.y() / float(self.surface().height())
        # resize the layout
        self.surface().pageLayout().fit(self.viewport().size(), self.viewMode())
        self.surface().pageLayout().update()
        # restore our position
        newPos = QPoint(round(x * self.surface().width()), round(y * self.surface().height()))
        diff = newPos - self._centerPos
        v = self.verticalScrollBar()
        h = self.horizontalScrollBar()
        v.setValue(v.value() + diff.y())
        h.setValue(h.value() + diff.x())

    def zoom(self, scale, pos=None):
        """Changes the display scale (1.0 is 100%).
        
        If pos is given, keeps that point at the same place if possible.
        Pos is a QPoint relative to ourselves.
        
        """
        if scale < 0.05 or scale > 3.0:
            return
        
        v = self.verticalScrollBar()
        h = self.horizontalScrollBar()
        
        if pos is None:
            pos = QPoint(self.width(), self.height()) / 2
        
        surfacePos = pos - self.surface().pos()
        page = self.surface().pageLayout().pageAt(surfacePos)
        if page:
            pagePos = surfacePos - page.pos()
            x = pagePos.x() / float(page.width())
            y = pagePos.y() / float(page.height())
            self.setScale(scale)
            newPos = QPoint(round(x * page.width()), round(y * page.height())) + page.pos()
        else:
            x = surfacePos.x() / float(self.surface().width())
            y = surfacePos.y() / float(self.surface().height())
            self.setScale(scale)
            newPos = QPoint(round(x * self.surface().width()), round(y * self.surface().height()))
        
        diff = newPos - surfacePos
        v.setValue(v.value() + diff.y())
        h.setValue(h.value() + diff.x())
            
    def zoomIn(self, pos=None, factor=1.1):
        self.zoom(self.scale() * factor, pos)
        
    def zoomOut(self, pos=None, factor=1.1):
        self.zoom(self.scale() / factor, pos)
        
    def wheelEvent(self, ev):
        if (self._wheelZoomEnabled and
            int(ev.modifiers()) & _SCAM == self._wheelZoomModifier):
            factor = 1.1 ** (ev.delta() / 120)
            if ev.delta():
                self.zoom(self.scale() * factor, ev.pos())
        else:
            super(View, self).wheelEvent(ev)

