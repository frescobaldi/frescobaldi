# This file is part of the qpopplerview package.
#
# Copyright (c) 2010 - 2014 by Wilbert Berendsen
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


from PyQt5.QtCore import QPoint, QSize, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QHelpEvent
from PyQt5.QtWidgets import QScrollArea, QStyle, QPinchGesture, QGestureEvent

from math import sqrt
import copy
from . import surface
from .kineticscrollarea import KineticScrollArea
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


class View(KineticScrollArea):
    
    MAX_ZOOM = 4.0
    
    viewModeChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        
        self.setAlignment(Qt.AlignCenter)
        self.setBackgroundRole(QPalette.Dark)
        self.setMouseTracking(True)

        self._viewMode = FixedScale
        self._wheelZoomEnabled = True
        self._wheelZoomModifier = Qt.CTRL
        
        self._pinchStartFactor = None
        super(View, self).grabGesture(Qt.PinchGesture)

        # delayed resize
        self._centerPos = False
        self._resizeTimer = QTimer(singleShot = True, timeout = self._resizeTimeout)
        
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
        # For some reason mouse tracking *must* be enabled on the child as well...
        sf.setMouseTracking(True)
        self.kineticScrollingActive.connect(sf.updateKineticCursor)

    
    def viewMode(self):
        """Returns the current ViewMode."""
        return self._viewMode
        
    def setViewMode(self, mode):
        """Sets the current ViewMode."""
        if mode == self._viewMode:
            return
        self._viewMode = mode
        if mode:
            self.fit()
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
        # don't do a fit() before the very first resize as the size is then bogus
        if self.viewMode():
            self.fit()
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
        rect &= self.surface().rect()
        return self.surface().pageLayout().pagesAt(rect)

    def redraw(self):
        """Redraws, e.g. when you changed rendering hints or papercolor on the document."""
        pages = list(self.visiblePages())
        documents = set(page.document() for page in pages)
        for document in documents:
            cache.clear(document)
        for page in pages:
            page.repaint()

    def fit(self):
        """(Internal). Fits the layout according to the view mode.
        
        Prevents scrollbar/resize loops by precalculating which scrollbars will appear.
        
        """
        mode = self.viewMode()
        if mode == FixedScale:
            return
        
        maxsize = self.maximumViewportSize()
        
        # can vertical or horizontal scrollbars appear?
        vcan = self.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
        hcan = self.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
        
        # width a scrollbar takes off the viewport size
        framewidth = 0
        if self.style().styleHint(QStyle.SH_ScrollView_FrameOnlyAroundContents, None, self):
            framewidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth) * 2
        scrollbarextent = self.style().pixelMetric(QStyle.PM_ScrollBarExtent, None, self) + framewidth
        
        # first try to fit full size
        layout = self.surface().pageLayout()
        layout.fit(maxsize, mode)
        layout.reLayout()
        
        # minimal values
        minwidth = maxsize.width()
        minheight = maxsize.height()
        if vcan:
            minwidth -= scrollbarextent
        if hcan:
            minheight -= scrollbarextent
        
        # do width and/or height fit?
        fitw = layout.width() <= maxsize.width()
        fith = layout.height() <= maxsize.height()
        
        if not fitw and not fith:
            if vcan or hcan:
                layout.fit(QSize(minwidth, minheight), mode)
        elif mode & FitWidth and fitw and not fith and vcan:
            # a vertical scrollbar will appear
            w = minwidth
            layout.fit(QSize(w, maxsize.height()), mode)
            layout.reLayout()
            if layout.height() <= maxsize.height():
                # now the vert. scrollbar would disappear!
                # enlarge it as long as the vertical scrollbar would not be needed
                while True:
                    w += 1
                    layout.fit(QSize(w, maxsize.height()), mode)
                    layout.reLayout()
                    if layout.height() > maxsize.height():
                        layout.fit(QSize(w - 1, maxsize.height()), mode)
                        break
        elif mode & FitHeight and fith and not fitw and hcan:
            # a horizontal scrollbar will appear
            h = minheight
            layout.fit(QSize(maxsize.width(), h), mode)
            layout.reLayout()
            if layout.width() <= maxsize.width():
                # now the horizontal scrollbar would disappear!
                # enlarge it as long as the horizontal scrollbar would not be needed
                while True:
                    h += 1
                    layout.fit(QSize(maxsize.width(), h), mode)
                    layout.reLayout()
                    if layout.width() > maxsize.width():
                        layout.fit(QSize(maxsize.width(), h - 1), mode)
                        break
        layout.update()
        
    def resizeEvent(self, ev):
        super(View, self).resizeEvent(ev)
        # Adjust the size of the document if desired
        if self.viewMode() and any(self.surface().pageLayout().pages()):
            if self._centerPos is False:
                self._centerPos = QPoint(0, 0)
            elif self._centerPos is None:
                # store the point currently in the center
                self._centerPos = self.viewport().rect().center() - self.surface().pos()
            if not self._resizeTimer.isActive():
                self._resizeTimeout()
            self._resizeTimer.start(150)
    
    def _resizeTimeout(self):
        if self._centerPos is None:
            return
        oldSize = self.surface().size()
        # resize the layout
        self.fit()
        # restore our position
        newSize = self.surface().size()
        newx = self._centerPos.x() * newSize.width() // oldSize.width()
        newy = self._centerPos.y() * newSize.height() // oldSize.height()
        # we explicitly want the non-kinetic centering function regardless of kinetic state.
        self.fastCenter(QPoint(newx, newy))
        self._centerPos = None

    def zoom(self, scale, pos=None):
        """Changes the display scale (1.0 is 100%).
        
        If pos is given, keeps that point at the same place if possible.
        Pos is a QPoint relative to ourselves.
        
        """
        scale = max(0.05, min(self.MAX_ZOOM, scale))
        if scale == self.scale():
            return
        
        if self.surface().pageLayout().count() == 0:
            self.setScale(scale)
            return
            
        if pos is None:
            pos = self.viewport().rect().center()
        
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
        surfacePos = pos - self.surface().pos()
        # use fastScrollBy as we do not want kinetic scrolling here regardless of its state.
        self.fastScrollBy(newPos - surfacePos)
            
    def zoomIn(self, pos=None, factor=1.1):
        self.zoom(self.scale() * factor, pos)
        
    def zoomOut(self, pos=None, factor=1.1):
        self.zoom(self.scale() / factor, pos)
        
    def wheelEvent(self, ev):
        if (self._wheelZoomEnabled and
            int(ev.modifiers()) & _SCAM == self._wheelZoomModifier):
            factor = 1.1 ** (ev.angleDelta().y() / 120)
            if ev.angleDelta().y():
                self.zoom(self.scale() * factor, ev.pos())
        else:
            super(View, self).wheelEvent(ev)
    
    def mousePressEvent(self, ev):
        """Mouse press event handler. Passes the event to the surface, and back to
        the base class if the surface did not do anything with it."""
        if not self.surface().handleMousePressEvent(ev):
            super(View, self).mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        """Mouse release event handler. Passes the event to the surface, and back to
        the base class if the surface did not do anything with it."""
        if not self.surface().handleMouseReleaseEvent(ev):
            super(View, self).mouseReleaseEvent(ev)

    def mouseMoveEvent(self, ev):
        """Mouse move event handler. Passes the event to the surface, and back to
        the base class if the surface did not do anything with it."""
        if self.kineticIsIdle():
            if self.surface().handleMouseMoveEvent(ev):
                return
        super(View, self).mouseMoveEvent(ev)

    def moveEvent(self, ev):
        """Move event handler. Passes the event to the surface if we've not started any kinetic move,
        and back to the base class if the surface did not do anything with it."""
        if self.kineticIsIdle():
            if self.surface().handleMoveEvent(ev):
                return
        super(View, self).moveEvent(ev)

    def event(self, ev):
        if isinstance(ev, QHelpEvent):
            if self.surface().handleHelpEvent(ev):
                ev.accept()
                return True
        if isinstance(ev, QGestureEvent):
            if self.gestureEvent(ev):
                ev.accept() # Accepts all gestures in the event
                return True
        
        return super(View, self).event(ev)
    
    def gestureEvent(self, event):
        """Gesture event handler. Return False if event is not accepted.
        Currently only cares about PinchGesture. Could also handle Swipe
        and Pan gestures."""
        pinch = event.gesture(Qt.PinchGesture)
        if pinch:
            return self.pinchGesture(pinch)
        return False

    def pinchGesture( self, gesture ):
        """Pinch gesture event handler. Return False if event is not accepted.
        Currently only cares about ScaleFactorChanged and not
        RotationAngleChanged."""

        # Gesture start? Reset _pinchStartFactor in case we didn't
        # catch the finish event
        if gesture.state() == Qt.GestureStarted:
            self._pinchStartFactor = None

        changeFlags = gesture.changeFlags()
        if changeFlags & QPinchGesture.ScaleFactorChanged:
            factor = gesture.property("scaleFactor")
            if not self._pinchStartFactor: # Gesture start?
                self._pinchStartFactor = self.scale()
            self.zoom(self._pinchStartFactor * factor,
                      self.mapFromGlobal(gesture.hotSpot().toPoint()) )

        # Gesture finished?
        if gesture.state() in (Qt.GestureFinished, Qt.GestureCanceled):
            self._pinchStartFactor = None

        return True

    def currentPage(self):
        """Returns the Page currently mostly in the center, or None if there are no pages."""
        pos = self.viewport().rect().center() - self.surface().pos()
        layout = self.surface().pageLayout()
        if len(layout):
            d = layout.spacing() * 2
            for dx, dy in ((0, 0), (-d, 0), (0, -d), (d, 0), (0, d)):
                dist = QPoint(dx, dy)
                page = layout.pageAt(pos + dist)
                if page:
                    return page
    
    def currentPageNumber(self):
        """Returns the number (index in the layout) of the currentPage(), or -1 if there are no pages."""
        page = self.currentPage()
        if page:
            return self.surface().pageLayout().index(page)
        return -1

    def gotoPageNumber(self, num):
        """Aligns the page at the given index in the layout to the topleft of our View."""
        layout = self.surface().pageLayout()
        if num < len(layout) and num != self.currentPageNumber():
            margin = QPoint(layout.margin(), layout.margin())
            self.scrollBy(layout[num].pos() + self.surface().pos() - margin)
            
    def position(self):
        """Returns a three-tuple(num, x, y) describing the page currently in the center of the View.
        
        the number is the index of the Page in the Layout, and x and y are the coordinates in the
        range 0.0 -> 1.0 of the point that is at the center of the View.
        
        This way a position can be retained even if the scale or the orientation of the Layout changed.
        
        Returns None, None, None if the layout is empty.
        
        """
        page = self.currentPage()
        if page:
            layout = self.surface().pageLayout()
            pos = self.viewport().rect().center() - self.surface().pos()
            pagePos = pos - page.pos()
            x = pagePos.x() / float(page.width())
            y = pagePos.y() / float(page.height())
            return layout.index(page), x, y
        return None, None, None

    def setPosition(self, position, overrideKinetic=False):
        """Sets the position to a three-tuple as previously returned by position().
        
        Setting overrideKinetic to true allows for fast setup, instead of scrolling all the way to the visible point.
        """
        layout = self.surface().pageLayout()
        pageNum, x, y = position
        if pageNum is None or pageNum >= len(layout):
            return
        page = layout[pageNum]
        # center this point
        newPos = QPoint(round(x * page.width()), round(y * page.height())) + page.pos()
        if overrideKinetic:
            self.fastCenter(newPos)
        else:
            self.center(newPos)
